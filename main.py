import json
import re
import requests
from collections import defaultdict
from bs4 import BeautifulSoup
from openai import OpenAI

BASE_URL = "https://www.notion.so"
START_URL = "https://www.notion.so/help"
MAX_DEPTH = 1
client = OpenAI()


class NotionExtractor:
    def __init__(self):
        # dictionary to capture content on
        self.url_content = defaultdict(list)

    # page method to go through all pages and extract content which contain text
    def get_page(self, url, depth=0):
        content = self.url_content.get(url, [])
        if content or depth > MAX_DEPTH:  # Skip if already visited or max depth reached
            return
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        page_elements = []

        # these tags are the ones that contain text, ignore anything else
        desired_tags = ["h1", "h2", "h3", "p", "ul", "ol", "div", "span"]
        for element in soup.find_all(lambda tag: tag.name in desired_tags):
            # for list items, combine all their elements into one line
            if element.name in ["ul", "ol"]:
                list_items = [li.get_text(strip=True) for li in element.find_all("li")]
                if list_items:
                    page_elements.append(",".join(list_items))
            else:
                text = element.get_text(strip=True)
                if text:  # Only print if the tag contains text
                    last_text = page_elements[-1] if page_elements else None
                    if last_text != text:
                        page_elements.append(text)

        # combine string into chunks and filter unnecessary info
        self.url_content[url] = self.filter_unnecessary_info(
            self.combine_strings(page_elements)
        )

        # log check to see what the strings look like
        print(f"Extracted content from {url}: {self.url_content[url]}")

        # get all the links
        links = soup.find_all("a", href=True)
        for link in links:
            target = link["href"]
            if (
                target.startswith("/")
                and "help" in target
                and "#" not in target
                and "academy" not in target
            ):
                target = BASE_URL + target
                self.get_page(target, depth + 1)

    def filter_unnecessary_info(self, string_list):
        # Remove text blobs containing these substrings, they add no value to the notion tutorial
        unwanted_substrings = [
            "ProductAIIntegrated AI assistantDocsSimple &",
            "AIIntegrated AI assistantDocsSimple",
            "TemplatesSetups",
            "ProductAIDocsWikisProjectsCalendarSitesTemplatesTeamsIndividualsDownloadPricingRequest",
            "Help Center",
        ]

        # Use the filter() function to exclude unwanted strings
        filtered_list = [
            string
            for string in string_list
            if all(substring not in string for substring in unwanted_substrings)
        ]

        return filtered_list

    # combine strings into chunks with a specified max length
    # this allows content to be processed in smaller pieces before sending to GPT
    def combine_strings(self, string_list, max_length=750):
        result = []
        current_combination = ""

        for string in string_list:
            if len(string) > max_length:
                string = string[:max_length]

            if len(current_combination) + len(string) + 1 > max_length:
                result.append(current_combination.strip())
                current_combination = string
            else:
                current_combination += " " + string

        if current_combination:
            result.append(current_combination.strip())

        return result

    def write_to_local(self):
        with open("notion_content.json", "w") as f:
            json.dump(self.url_content, f, indent=4)

    def gpt_enrich(self):
        # final enriched chunks
        final_chunks = []
        if len(self.url_content) == 0:
            self.url_content = json.load(open("notion_content.json"))

        for _, v in self.url_content.items():
            gpt_messages = []
            for line in v:
                gpt_messages.append({"role": "user", "content": line})

            gpt_messages.append(
                {
                    "role": "user",
                    "content": "For all of the above content, comprehend the text and rephrase in plain english their content. do not exceed 750 characters for each line.",
                }
            )

            completion = client.chat.completions.create(
                model="gpt-4o", messages=gpt_messages
            )

            for completion in completion.choices:
                content = completion.message.content
                sections = re.split(r"\n\d+\.\s", content)
                trimmed_sections = [
                    section.strip() for section in sections if section.strip()
                ]
                for section in trimmed_sections:
                    final_chunks.append(section)

        # Write the enriched content to a file
        with open("enriched_content.json", "w") as f:
            json.dump(final_chunks, f, indent=4)

        return final_chunks


# simply run python main.py to execute
extract = NotionExtractor()
extract.get_page(START_URL)
extract.write_to_local()
extract.gpt_enrich()
