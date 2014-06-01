from bs4 import BeautifulSoup


def get_county_name(json_response):
    soup = BeautifulSoup(entries)
    smalls = soup("small")
    for s in smalls:
        if s.string and 'county' in s.string.lower():
            return s.string

