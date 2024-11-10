import re
import requests
import json
from lxml import html
from datetime import date

# Next Year
NEXT_YEAR = str(date.today().year + 1)

# Current Hebrew Year
CURRENT_HEBREW_YEAR = 'תשפ"ה'

# TAU Constants
# TAU_URL = 'https://go.tau.ac.il/he/med?degree=drMedicine'
TAU_URL = 'https://go.tau.ac.il/graphql'
TAU_PAYLOAD = {"operationName": "getPrograms",	"variables": {"search": {"isSearch": True, "langcode": "he", "type": "program", "faculty": "0100", "degree": "ד\"ר לרפואה"}}, "query": "query getPrograms($search: JSON!) {\n  getPrograms(search: $search) {\n    results {\n      nid\n      title\n      langcode\n      field_reference_combine_programs\n      field_short_description\n      field_studying_year_number\n      mamta_title\n      field_learning_aspect\n      field_interest_area\n      field_faculty_mamta\n      field_faculty_mamta_1\n      field_degree_type\n      field_comments\n      field_semester\n      field_external_department_id\n      field_mamta_programs\n      field_plain_id_programs\n      field_registration_comments\n      field_plain_faculty_id\n      field_short_name\n      type\n      body\n      field_weight_for_faculty_nested\n      field_faculty_nid\n      field_bi_interested_number\n      field_bi_degree_number\n      field_bi_faculty_number\n      field_bi_degree_description\n      field_bi_interested_description\n      field_bi_faculty_description\n      __typename\n    }\n    __typename\n  }\n}\n"}
TAU_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/93.0.4577.63 Safari/537.36',
        'host': 'go.tau.ac.il',
        "Content-type": "application/json",
    }
TAU_XPATH = "//div[div[div[div[a[contains(@href, '8215')]]]] and contains(@class, 'wrapper')]//p[contains(text(), '.')]"
TAU_REG = re.compile(r"\b\d{3}\.\d{2}\b")
TAU = 'TAU'

# HUJI Constants
HUJI_URL = 'https://info.huji.ac.il/bachelor/Medicine'
HUJI_XPATH = "//p[span[@data-toggle='tooltip']]"
HUJI_REG = re.compile(r"\b\d{2}\.\d{3}\b")
HUJI = 'HUJI'

# TECH Constants
TECH_URL = 'https://admissions.technion.ac.il/sechem-for-admission/sekem/'
# TECH_XPATH = "//tr[td[contains(text(), 'מגמת רפואה')]]//td[@class='column-2' or @class='column-3']"
TECH_XPATH = "//tr[td[contains(text(), 'מגמת רפואה')]]//td[@class='column-2']"
TECH = 'TECH'

# BGU Constants
# BGU_URL = 'https://www.bgu.ac.il/welcome/ba/catalog/categories/medical-school/?tab=2944'
BGU_URL = 'https://www.bgu.ac.il/umbraco/api/AcceptanceConditions/GetAcceptanceConditions'
BGU_PAYLOAD = {"cultureCode": "he-IL", "campusId": "0", "year": NEXT_YEAR, "semester": "1", "path": "1", "specialization": None, "departmentId": 471}
BGU_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/93.0.4577.63 Safari/537.36',
        "Content-type": "application/json",
    }
BGU_XPATH = "//div[@id='title-description' and contains(text(), 'סכם')]"
BGU_REG = re.compile(r"\d{3}\b")
BGU = 'BGU'

# Error Logs:
INTERNAL_SERVER_ERROR = "Internal Server Error"


# Initiates an API Request of a specific university
def uni_api_req(url, headers, payload):
    return requests.post(url, headers=headers, json=payload)


# Crawls a remote UNI site
def crawl_uni_site(url, uni_xpath, uni):
    # Crawls the remote UNI site
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/93.0.4577.63 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': url
    }
    response = requests.get(url, headers=headers)

    # Parses the HTML content
    tree = html.fromstring(response.content)

    # Uses XPath to find all the required elements
    paragraphs = tree.xpath(uni_xpath)

    # Filters the sentences from the selected paragraphs
    filtered_sentences = []
    for paragraph in paragraphs:
        # Get the text content of the paragraph
        text = paragraph.text_content()

        # Splits the text into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)

        # Check each sentence for the specific UNI pattern. If so, appends sentence to list
        for sentence in sentences:
            if is_pattern(sentence, uni):
                filtered_sentences.append(sentence.strip())

    return filtered_sentences


# Checks if the given line is valid according to the pattern of the given university
def is_pattern(sentence, uni):
    if uni == HUJI:
        # Define the regex pattern for xx.xxx format
        return CURRENT_HEBREW_YEAR in sentence and HUJI_REG.search(sentence)
    elif uni == TAU:
        return TAU_REG.search(sentence)
    elif uni == TECH:
        return True
    elif uni == BGU:
        return BGU_REG.search(sentence)
    return False


# Retrieves BGU Values
def fetch_value_from_bgu():
    # Crawls remote BGU site
    bgu_fetched_raw_data = uni_api_req(BGU_URL, BGU_HEADERS, BGU_PAYLOAD)

    try:
        # Results
        bgu_text_raw_data = json.loads(bgu_fetched_raw_data.text)['items'][0]
        bgu_output2reformat = ['סכם: ' + bgu_text_raw_data['psycho_sekem'] + ' ' + bgu_text_raw_data['psycho_and_or'].strip() + ' פסיכו: ' + bgu_text_raw_data['psycho_value']]

        # Creates BGU output string
        bgu_output_str = reformat_output(bgu_output2reformat, BGU)

        return bgu_output_str

    except json.decoder.JSONDecodeError:
        return INTERNAL_SERVER_ERROR


# Retrieves HUJI Values
def fetch_value_from_huji():
    # Crawls remote HUJI site
    huji_fetched_raw_data = crawl_uni_site(HUJI_URL, HUJI_XPATH, HUJI)

    # Organizes Relevant Lines
    huji_thresholds = [line.strip('.').split("'")[-1] for line in huji_fetched_raw_data]

    # Creates HUJI output string
    huji_output_str = reformat_output(huji_thresholds, HUJI)

    return huji_output_str


# Retrieves TECH Values
def fetch_value_from_tech():
    # Crawls remote TECH site
    tech_fetched_raw_data = crawl_uni_site(TECH_URL, TECH_XPATH, TECH)

    # Organizes Relevant Lines
    tech_raw_lines = tech_fetched_raw_data[0].split('\n')
    tech_thresholds = [tech_raw_lines[1] + ': ' + tech_raw_lines[0], tech_raw_lines[2]]

    # Creates TECH output string
    tech_output_str = reformat_output(tech_thresholds, TECH)

    return tech_output_str


# Retrieves TAU Values
def fetch_value_from_tau():
    # API Request
    response = uni_api_req(TAU_URL, TAU_HEADERS, TAU_PAYLOAD)

    try:
        # Results
        tau_programs_data = json.loads(response.text)['data']['getPrograms']['results']

        # Catches Relevant Med Program
        med_data = [prog_data for prog_data in tau_programs_data if prog_data['nid'] == '8215'][0]

        # Extracts Only Relevant Lines
        data_without_html_tags = med_data['field_registration_comments'].replace('&nbsp;', '').replace('<', '').replace('//', '').split('p>')
        tau_thresholds = [update.strip('/') for update in data_without_html_tags if any(char.isdigit() for char in update)]

        # Creates TAU output string
        tau_output_str = reformat_output(tau_thresholds, TAU)

        return tau_output_str

    except json.decoder.JSONDecodeError:
        return INTERNAL_SERVER_ERROR


# Reformat the data as a nice string
def reformat_output(data_lst, uni):
    # Current UNI
    outputs_str = '%s:\n' % uni

    # Concatenates lines
    for line in data_lst:
        outputs_str += (line + '\n')

    return outputs_str


# Call the functions and print the results
def main():
    print(fetch_value_from_huji())
    print(fetch_value_from_tech())
    print(fetch_value_from_tau())
    print(fetch_value_from_bgu())


# Main Function
if __name__ == '__main__':
    main()
