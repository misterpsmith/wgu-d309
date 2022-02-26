import os
import posixpath
import requests
from urllib.parse import urlsplit, unquote

# Download image_predictions.tsv via requests from the provided URL.

# Provided URL.
url = "https://d17h27t6h515a5.cloudfront.net/topher/2017/August/599fd2ad_image-predictions/image-predictions.tsv"

# Extract file name.
path = urlsplit(url).path
file_name = posixpath.basename(unquote(path))

# Get data from URL via requests library.
url_data = requests.get(url)

# If file exists, do nothing, else write the data to a file.
if not os.path.isfile(file_name):
    with open(file_name, 'wb') as file:
        file.write(url_data.content)
    print("%s file downloaded." % file_name)
else:
    print("%s file exists." % file_name)
