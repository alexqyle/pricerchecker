# How to run it
## Setup
1. Install Python 3.9.
2. Run `pip install -r requirements.txt`.
3. Create configuration file `config.yaml`. See [below](#configuration-file-example)
4. Run `python ./src/price_checker.py --config ./config.yaml`.

## Configuration file example
```yaml
price_selectors:  # css selectors to fetch price for different sites
  - selector_name: site1_selector
    decimal_integer_selector: div#app div.product-price > ul > li.price-current > strong
    decimal_fraction_selector: div#app div.product-price > ul > li.price-current > sup
  - selector_name: site2_selector
    full_price_selector: span.a-color-price
  - selector_name: site3_selector
    full_price_selector: div[class*="pricingContainer"] span[class*="screenReaderOnly"]
special_tweaks:  # special request tweaks for some sites
  - tweak_name: site2_tweak
    cookies:
      - i18n-prefs: CAD
  - tweak_name: site3_tweak
    cookies:
      - some_cookie: cookie_value
    headers:
      - some_header: header_value
item_groups:
  - disabled: false  # enable this group (default to `false`)
    group_name: Product 1
    items:
      - name: site1 Product 1 - 1
        url: https://www.site1.com/product_1_1
        price_selector: site1_selector  # refer to `selector_name` defined above
      - name: site1 Product 1 - 2
        url: https://www.site1.com/product_1_2
        price_selector: site1_selector
        get_price_delay: 2  # add waiting time in seconds before fetching price
      - name: site2 Product 1 - 1
        url: https://www.site2.com/product_1_1
        price_selector: site2_selector
        special_tweak: site2_tweak  # refer to `tweak_name` defined above
        get_price_delay: 3
      - disabled: true  # disable single item
      - name: site2 Product 1 - 2
        url: https://www.site2.com/product_1_2
        price_selector: site2_selector
        special_tweak: site2_tweak
  - disabled: true  # disable entire group
    group_name: Product 2
    items:
      - name: site1 Product 2 - 1
        url: https://www.site1.com/product_2_1
        price_selector: newegg_selector
      - name: site2 Product 2 - 1
        url: https://www.site2.com/product_2_1
        price_selector: site2_selector
        special_tweak: site2_tweak
      - name: site3 Product 2 - 1
        url: https://www.site3.com/product_2_1
        price_selector: site3_selector
        special_tweak: site3_tweak
data_exporters:  # only support google sheet for now
  - type: google_sheet
    google_service_account_key_file: /path/to/server_account_key.json
    spreadsheet_id: google_spreadsheet_id

```