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
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
import typer
from webdriver_manager.chrome import ChromeDriverManager

ACCEPTABLE_EXT = ["jpg", "jpeg", "png", "webp"]
CHROMEDRIVER_PATH = "/usr/lib/chromium-browser/chromedriver"
TMP_PATH = "/data/dataset/CondensedMovies/metadata/casts.csv"


def crawl_google_image(
    driver: webdriver.Chrome,
    query: str,
    limit: int = 10,
    download_dir: str = "/data/imdb-actor-image",
):
    download_dir = Path(download_dir) / query
    download_dir.mkdir(parents=True, exist_ok=True)

    count = {
        "success": len(list(download_dir.glob("*.*"))),
        "fail": 0,
    }

    if count["success"] >= limit:
        return

    large_limit = count["success"] + int(limit * 1.5)
    elem = driver.find_element(By.NAME, "q")
    elem.send_keys(query)
    elem.send_keys(Keys.RETURN)

    try:
        WebDriverWait(driver, 1).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "img.rg_i.Q4LuWd"))
        )
    except TimeoutError:
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "img.rg_i.Q4LuWd"))
            )
        except TimeoutError:
            return

    img_element_list = list(driver.find_elements(By.CSS_SELECTOR, "img.rg_i.Q4LuWd"))

    last_height = driver.execute_script("return document.body.scrollHeight")
    while len(img_element_list) < large_limit:
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        sleep(0.1)

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
        )

    img_element_list = img_element_list[count["success"] :]

    for img in img_element_list:
        if count["success"] >= limit:
            break

        try:
            img.click()
            WebDriverWait(driver, 1).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        '//*[@id="Sva75c"]/div[2]/div/div[2]/div[2]/div[2]/c-wiz/div[2]/div[1]/div[1]/div[2]/div/a/img',
                    )
                )
            )
            image_src = driver.find_element(
                By.XPATH,
                '//*[@id="Sva75c"]/div[2]/div/div[2]/div[2]/div[2]/c-wiz/div[2]/div[1]/div[1]/div[2]/div/a/img',
            ).get_attribute("src")
        except:
            count["fail"] += 1
            continue

        ext = image_src.split("?")[0].split(".")[-1].lower()

        if ext in ACCEPTABLE_EXT:
            image_path = download_dir / f"{count['success']:03d}.{ext}"
            image_path = str(image_path.absolute())

            try:
                urllib.request.urlretrieve(image_src, image_path)
                count["success"] += 1
            except Exception as e:
                print(f"ERROR [{query}] {count['fail']:03d} - {image_src}")
                print(e)
                count["fail"] += 1


def main(start: int = 0, end: int = 100):
    cast_df = pd.read_csv(TMP_PATH)

    cast_list = list()
    for idx, row in cast_df.iterrows():
        # row: imdbid, cast
        try:
            parsed_json = ast.literal_eval(row[1])
            cast_list.extend(list(parsed_json.keys()))
        except Exception as e:
            print(f"ERROR {idx} - {e}")

    actor_list = sorted(list(set(cast_list)))
    actor_list = actor_list[start:end]

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36"
    )
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options,
    )
    driver.get("https://www.google.co.kr/imghp?hl=en")

    for actor_name in tqdm(actor_list):
        crawl_google_image(
            driver,
            query=actor_name,
            limit=10,
            download_dir="/data/imdb-actor-image",
        )


if __name__ == "__main__":
    typer.run(main)
