import time
from pprint import pprint

import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm.auto import tqdm

# repo = "PyTorch/pytorch"
repo = "PyTorchLightning/pytorch-lightning"
scope = "REPOSITORY"
# scope = "PACKAGE"
url = f'https://github.com/{repo}/network/dependents?dependent_type={scope}'
fetching = []

pbar = tqdm(desc="fetching...")
while True:
    dep = requests.get(url, timeout=10)
    html = dep.content.decode(dep.encoding)
    soup = BeautifulSoup(html, "html.parser")

    page = [
        dict(
            org=box.find('a', {
                "data-repository-hovercards-enabled": ""
            }).text,
            repo=box.find('a', {
                "data-hovercard-type": "repository"
            }).text,
            stars=int(box.find_all('span', {"class": "pl-3"})[0].text.replace(",", "")),
            forks=int(box.find_all('span', {"class": "pl-3"})[1].text.replace(",", "")),
        ) for box in soup.findAll("div", {"class": "Box-row"})
    ]
    pagination = soup.find("div", {"class": "paginate-container"})
    if not pagination:
        print(f"unexpected page: {url}")
        time.sleep(9)
        continue
    fetching += page
    nav_hrefs = pagination.find_all('a')
    if "next" not in [href.text.lower() for href in nav_hrefs]:
        break
    url = nav_hrefs[-1]["href"]
    pbar.update()

# pprint(fetching)
pprint(len(fetching))

stats = pd.DataFrame(fetching).sort_values("stars", ascending=False)
stats["URL"] = [f"https://github.com/{row['org']}/{row['repo']}" for _, row in stats.iterrows()]
stats.drop_duplicates().to_csv(f"dependents{repo.replace('/', '-')}-{scope}.csv", index=None)
