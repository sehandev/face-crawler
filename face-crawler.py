import ast
from pathlib import Path
from time import sleep
from tqdm.auto import tqdm
import urllib.request
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

ACCEPTABLE_EXT = ["jpg", "jpeg", "png", "webp"]
CHROMEDRIVER_PATH = "/usr/lib/chromium-browser/chromedriver"
TMP_PATH = "/data/dataset/CondensedMovies/metadata/casts.csv"


def crawl_google_image(
    query: str,
    limit: int = 10,
    download_dir: str = "/data/imdb-actor-image",
):
    large_limit = int(limit * 1.5)

    download_dir = Path(download_dir) / query
    download_dir.mkdir(parents=True, exist_ok=True)

    count = {
        "success": len(list(download_dir.glob("*.*"))),
        "fail": 0,
    }

    if count["success"] >= limit:
        return

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36"
    )
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options,
    )

    driver.get("https://www.google.co.kr/imghp?hl=en")
    elem = driver.find_element(By.NAME, "q")
    elem.send_keys(query)
    elem.send_keys(Keys.RETURN)

    sleep(2)

    last_height = driver.execute_script("return document.body.scrollHeight")

    img_element_list = list()
    while len(img_element_list) < large_limit:
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        sleep(1)

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            try:
                # 결과 더보기
                driver.find_element(".mye4qd").click()
            except:
                break
        last_height = new_height

        img_element_list = list(
            driver.find_elements(By.CSS_SELECTOR, "img.rg_i.Q4LuWd")
        )[count["success"] :]

    for img in img_element_list:
        if count["success"] >= limit:
            break

        try:
            img.click()
        except:
            count["fail"] += 1
            continue

        sleep(0.5)

        image_src = driver.find_element(
            By.XPATH,
            '//*[@id="Sva75c"]/div[2]/div/div[2]/div[2]/div[2]/c-wiz/div[2]/div[1]/div[1]/div[2]/div/a/img',
        ).get_attribute("src")
        image_src = image_src.split("?")[0]
        ext = image_src.split(".")[-1]

        if ext.lower() in ACCEPTABLE_EXT:
            image_path = download_dir / f"{count['success']:03d}.{ext}"
            image_path = str(image_path.absolute())

            try:
                urllib.request.urlretrieve(image_src, image_path)
                count["success"] += 1
            except Exception as e:
                print(f"ERROR [{query}] {count['fail']:03d} - {image_src}")
                print(e)
                count["fail"] += 1


if __name__ == "__main__":
    cast_df = pd.read_csv(TMP_PATH)

    cast_list = list()
    for idx, row in cast_df.iterrows():
        # row: imdbid, cast
        try:
            parsed_json = ast.literal_eval(row[1])
            cast_list.extend(list(parsed_json.keys()))
        except Exception as e:
            print(f"ERROR {idx} - {e}")

    actor_list = list(set(cast_list))

    for actor_name in tqdm(actor_list):
        crawl_google_image(
            query=actor_name,
            limit=10,
            download_dir="/data/imdb-actor-image",
        )
