import os
from typing import Any, Dict, List
import re
from datetime import datetime
from collections import defaultdict

import feedparser

from bs4 import BeautifulSoup, element
import requests

from .processors import process_bylines

xml_urls = [
    "https://www.purdue.edu/newsroom/rss/academics.xml",
    "https://www.purdue.edu/newsroom/rss/AdvNews.xml",
    "https://www.purdue.edu/newsroom/rss/AgriNews.xml",
    "https://www.purdue.edu/newsroom/rss/BizNews.xml",
    "https://www.purdue.edu/newsroom/rss/community.xml",
    "https://www.purdue.edu/newsroom/rss/DiversityNews.xml",
    "https://www.purdue.edu/newsroom/rss/EdCareerNews.xml",
    "https://www.purdue.edu/newsroom/rss/EventNews.xml",
    "https://www.purdue.edu/newsroom/rss/faculty_staff.xml",
    "https://www.purdue.edu/newsroom/rss/FeaturedNews.xml",
    "https://www.purdue.edu/newsroom/rss/general.xml",
    "https://www.purdue.edu/newsroom/rss/HealthMedNews.xml",
    "https://www.purdue.edu/newsroom/rss/hrnews.xml",
    "https://www.purdue.edu/newsroom/rss/InfoTech.xml",
    "https://www.purdue.edu/newsroom/rss/LifeNews.xml",
    "https://www.purdue.edu/newsroom/rss/LifeSciNews.xml",
    "https://www.purdue.edu/newsroom/rss/OTCNews.xml",
    "https://www.purdue.edu/newsroom/rss/outreach.xml",
    "https://www.purdue.edu/newsroom/rss/PhysicalSciNews.xml",
    "https://www.purdue.edu/newsroom/rss/PRFAdminNews.xml",
    "https://www.purdue.edu/newsroom/rss/ResearchNews.xml",
    "https://www.purdue.edu/newsroom/rss/StudentNews.xml",
    "https://www.purdue.edu/newsroom/rss/VetMedNews.xml",
    "https://www.purdue.edu/newsroom/rss/AgNews.xml",
    "https://www.purdue.edu/newsroom/rss/DiscoParkNews.xml",
    "https://www.purdue.edu/newsroom/rss/EdNews.xml",
    "https://www.purdue.edu/newsroom/rss/engineering.xml",
    "https://www.purdue.edu/newsroom/rss/HHSNews.xml",
    "https://www.purdue.edu/newsroom/rss/ITaPNews.xml",
    "https://www.purdue.edu/newsroom/rss/CLANews.xml",
    "https://www.purdue.edu/newsroom/rss/LibrariesNews.xml",
    "https://www.purdue.edu/newsroom/rss/KrannertNews.xml",
    "https://www.purdue.edu/newsroom/rss/NEESnews.xml",
    "https://www.purdue.edu/newsroom/rss/NursingNews.xml",
    "https://www.purdue.edu/newsroom/rss/PharmacyNews.xml",
    "https://www.purdue.edu/newsroom/rss/president.xml",
    "https://www.purdue.edu/newsroom/rss/PRFNews.xml",
    "https://www.purdue.edu/newsroom/rss/ScienceNews.xml",
    "https://www.purdue.edu/newsroom/rss/TechNews.xml",
    "https://www.purdue.edu/newsroom/rss/VetNews.xml",
]


def directory_search(searchName: str) -> Dict[str, Any]:
    """Helper function to search names in the Purdue Directory

    Arguments:
        searchName (str): the name to be queried in the Purdue Directory.

    Returns:
        A Dict in Slack format.
    """
    requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += "HIGH:!DH:!aNULL"
    try:
        requests.packages.urllib3.contrib.pyopenssl.DEFAULT_SSL_CIPHER_LIST += (
            "HIGH:!DH:!aNULL"
        )
    except AttributeError:
        # no pyopenssl support used / needed / available
        pass

    # POST UP LEBRON!!!
    r = requests.post("https://purdue.edu/directory", data={"searchString": searchName})
    soup = BeautifulSoup(r.text, "html.parser")

    result = soup.findAll(id="results")

    ret_list = []

    for row in result[0].findAll("ul")[0].findAll("li"):
        tmp = []
        # find the name
        for h2 in row.findAll("h2"):
            tmp.append(h2.text)

        # find the rest of the information
        for td in row.findAll("td"):
            tmp.append(td.text)

        ret_list.append(tmp)

    result_str = "results" if len(ret_list) else "result"

    ret_blocks = {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f'Found *{len(ret_list)}* {result_str} for: "{searchName}"',
                },
            },
            {"type": "divider"},
        ]
    }

    for result in ret_list:
        ret_blocks["blocks"].append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{result[0]} \nemail: {result[2]}\ncampus: {result[3]}\ncollege: {result[4]}",
                },
            }
        )

    return ret_blocks


def get_pngs() -> List[List[str]]:
    """Retrieves a list of three-wide arrays from the Purdue PNG website.

    Returns:
        A list of rows representing information about PNGs.
    """
    r = requests.get(
        "https://www.purdue.edu/ehps/police/assistance/stats/personanongrata.html"
    )

    soup = BeautifulSoup(r.text, "html.parser")
    table = soup.find(summary="Persona nongrata list")

    ret_list = []

    for tr in table.find_all("tr"):
        td = tr.find_all("td")
        row = [i.text.strip() for i in td]
        if len(row) != 0:
            ret_list.append(row)

    return ret_list


def send_slack(title: str, link: str, date: str, is_pr: bool = False) -> None:
    """A helper function that sends messages to a specified Slack channel.

    Arguments:
        title (str): A string representing the title of the message.
        link (str): A string representing a possible link to attach with the message
        date (str): When the press release was released.
        is_pr (bool): A boolean representing whether the incoming Slack message
            is a press release or otherswise.

    Returns:
        None
    """
    if "http" not in link:
        link = "http://{}".format(link)

    headers = {
        "content-type": "application/json",
        "Authorization": "Bearer {}".format(os.getenv("SLACK_TOKEN")),
    }
    payload = {
        "channel": os.getenv("SLACK_CHANNEL"),
        "text": title,
        "blocks": [
            {"type": "section", "text": {"type": "mrkdwn", "text": f"{title}"}},
            {
                "type": "context",
                "elements": [{"type": "mrkdwn", "text": f"Posted on {date}"}],
            },
        ],
    }

    if is_pr:
        payload["blocks"][0]["text"] = {"type": "mrkdwn", "text": f"<{link}|{title}>"}
        payload["blocks"][0]["accessory"] = {
            "type": "button",
            "text": {"type": "plain_text", "text": "Take Me!"},
            "value": "take",
            "action_id": "button",
        }

    # logging.debug(payload)
    r = requests.post(
        "https://slack.com/api/chat.postMessage", headers=headers, json=payload
    )
    r.raise_for_status()


def get_bylines(query: str) -> List[Dict[str, Any]]:
    """Helper function to retrieve reporter bylines for the current payperiod.

    Returns:
        List[Dict[str, Any]]
        A list of Slack blocks containing reporter information.
    """

    date_regex_string = r"[0-9]*[0-9]/[0-9]*[0-9]/[12][09][012][0-9]"

    date_regex_match = re.findall(date_regex_string, query)

    if len(date_regex_match) == 2:
        start_str = date_regex_match[0]
        end_str = date_regex_match[1]
    else:
        d = datetime.now()
        if d.day <= 15:
            start_str = f"{d.month}/1/{d.year}"
            end_str = f"{d.month}/15{d.year}"
        else:
            start_str = f"{d.month}/16/{d.year}"
            end_str = f"{d.month}/{d.day}/{d.year}"

    campus_search_string = f"https://www.purdueexponent.org/search/?q=&nsa=eedition&t=article&c[]=campus&l=100&s=start_time&sd=desc&f=rss&d1={start_str}&d2={end_str}"
    city_search_string = f"https://www.purdueexponent.org/search/?q=&nsa=eedition&t=article&c[]=city_state&l=100&s=start_time&sd=desc&f=rss&d1={start_str}&d2={end_str}"
    sports_search_string = f"https://www.purdueexponent.org/search/?q=&nsa=eedition&t=article&c[]=sports&l=100&s=start_time&sd=desc&f=rss&d1={start_str}&d2={end_str}"

    campus_feed = feedparser.parse(campus_search_string)
    city_feed = feedparser.parse(city_search_string)
    sports_feed = feedparser.parse(sports_search_string)

    entry_list = campus_feed.entries + city_feed.entries + sports_feed.entries

    print(entry_list)

    bylines = process_bylines(entry_list)

    ret_blocks = {"blocks": []}

    ret_blocks["blocks"].append(
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{len(bylines.keys())} reporters wrote articles between {start_str} and {end_str}",
            },  # noqa
        }  # noqa
    )

    ret_blocks["blocks"].append({"type": "divider"})

    for reporter in bylines.keys():
        res_articles = ""
        for article in bylines[reporter]["articles"]:
            res_articles = res_articles + f"* {article}\n"
        res_string = f"{reporter}: {bylines[reporter]['count']} \n{res_articles}"
        ret_blocks["blocks"].append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": res_string,},  # noqa
            }  # noqa
        )

    return ret_blocks


def crime_scrape():
    r = requests.get(
        "https://www.purdue.edu/ehps/police/assistance/stats/statsdaily.html"
    )
    soup = BeautifulSoup(r.text, features="html.parser")

    crime_div = soup.find("article", {"class": "post clearfix"})

    # print(crime_div)

    ret_dict = defaultdict(lambda: [])
    key = ""
    is_key = False
    for p in crime_div.find_all("p"):
        # print(p.contents)
        cleaned_result = ""
        if len(p.contents) == 1:
            # check for tag
            if isinstance(p.contents[0], element.Tag):
                cleaned_list = [
                    c for c in p.contents[0].contents if not isinstance(c, element.Tag)
                ]
                cleaned_result = " ".join(cleaned_list).strip()
            else:
                # regex search
                match = re.findall(
                    r"([A-Z]+DAY [0-9]*[0-9]-[0-9]*[0-9]-[0-9][0-9])", p.contents[0]
                )
                print(match)
                if len(match) > 0:
                    cleaned_result = match[0]
                    is_key = True
        else:
            cleaned_list = [c for c in p.contents if not isinstance(c, element.Tag)]
            cleaned_result = " ".join(cleaned_list)

        if len(cleaned_result) < 1:
            continue

        match = re.findall(
            r"([A-Z]+DAY [0-9]*[0-9]-[0-9]*[0-9]-[0-9][0-9])", cleaned_result
        )
        print(match)
        if len(match) == 1 or is_key:
            key = cleaned_result
        else:
            ret_dict[key].append(cleaned_result)

        is_key = False

    for key in ret_dict:
        ret_dict[key] = list(ret_dict[key])

    return ret_dict


def get_quote() -> Dict[str, Any]:
    """Helper function to get and process daily quotes."""

    r = requests.get("http://api.quotable.io/random")

    data = r.json()

    tipp_daily_total = 0

    corona_r = requests.get(
        "https://hub.mph.in.gov/api/3/action/datastore_search?resource_id=8b8e6cd7-ede2-4c41-a9bd-4266df783145&q=Tippecanoe"
    )

    while len(corona_r.json()["result"]["records"]) > 0:
        corona_data = corona_r.json()["result"]
        tipp_daily_total += sum(
            [record["COVID_COUNT"] for record in corona_data["records"]]
        )
        corona_r = requests.get(
            "https://hub.mph.in.gov" + corona_data["_links"]["next"]
        )

    ret_blocks = {"blocks": []}

    ret_blocks["blocks"].append(
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"good morning! here's a quote to get your day started ʕ•́ᴥ•̀ʔっ\n\"{data['content']}\" - {data['author']}\nthere are {tipp_daily_total} COVID-19 cases in tippecanoe county, according to the isdh (╥﹏╥)",
            },  # noqa
        }  # noqa
    )

    headers = {
        "content-type": "application/json",
        "Authorization": "Bearer {}".format(os.getenv("SLACK_TOKEN")),
    }
    payload = {
        "channel": "random",
        "text": "",
        "blocks": ret_blocks["blocks"],
    }

    r = requests.post(
        "https://slack.com/api/chat.postMessage", headers=headers, json=payload
    )

    case_count_r = requests.get("https://hub.mph.in.gov/api/3/action/datastore_search_sql?sql=SELECT \"DATE\", sum(\"COVID_COUNT\") as count from \"46b310b9-2f29-4a51-90dc-3886d9cf4ac1\" where \"COUNTY_NAME\" = 'Tippecanoe' group by \"DATE\" order by \"DATE\" desc limit 30")

    records = case_count_r.json()["result"]["records"]

    for record in records:
        record["count"] = int(record["count"])
        record["DATE"] = datetime.fromisoformat(record["DATE"])

    counts = [record["count"] for record in records]
    dates = [record["DATE"] for record in records]

    plt.title("Cases reported in Tippecanoe County by day")

    plt.ylim(0, max(counts) + 5)
    plt.plot(dates, counts)
    plt.xticks(rotation=20)
    plt.savefig('/tmp/tmp1337.png', pad_inches=5)

    headers = {
        "content-type": "application/json",
        "Authorization": "Bearer {}".format(os.getenv("SLACK_TOKEN")),
    }
    payload = {
        "channel": "random",
        "text": "",
        "file": "/tmp/tmp1337.png",
    }

    r = requests.post(
        "https://slack.com/api/files.upload", headers=headers, json=payload
    )


    return ret_blocks
