from urllib.request import urlopen as uReq

import pymongo
# from flask_cors import CORS,cross_origin
import requests
from bs4 import BeautifulSoup as bs
from flask import Flask, render_template, request

app = Flask(__name__)  # initialising the flask app with the name 'app'

@app.route('/', methods=['POST', 'GET'])  # route with allowed methods as POST and GET
def index():
    if request.method == 'POST':
        searchString = request.form['content'].replace(" ", "")
        dbConn = pymongo.MongoClient("mongodb://localhost:27017/")  # opening a connection to Mongo
        db = dbConn['crawlerDB']  # connecting to the database called crawlerDB
        reviews = db[searchString].find({})  # searching the collection with the name same as the keyword
        if reviews.count() > 0:  # if there is a collection with searched keyword and it has records in it
            return render_template('results.html', reviews=reviews)  # show the results to user
        else:
            flipkart_url = "https://www.flipkart.com/search?q=" + searchString  # preparing the URL to search the product on flipkart
            uClient = uReq(flipkart_url)  # requesting the webpage from the internet
            flipkartPage = uClient.read()  # reading the webpage
            uClient.close()  # closing the connection to the web server
            flipkart_html = bs(flipkartPage, "html.parser")  # parsing the webpage as HTML
            bigboxes = flipkart_html.findAll("div", {"class": "_1AtVbE col-12-12"})  # seacrhing for appropriate tag to redirect to the product link
            del bigboxes[0:3]  # the first 3 members of the list do not contain relevant information, hence deleting them.
            box = bigboxes[0]  # taking the first iteration (for demo)
            productLink = "https://www.flipkart.com" + box.div.div.div.a['href']  # extracting the actual product link
            prodRes = requests.get(productLink)  # getting the product page from server
            prod_html = bs(prodRes.text, "html.parser")  # parsing the product page as HTML
            bigbox1 = prod_html.findAll("div", {"class": "_1AtVbE col-12-12"})
            box1 = bigbox1[-3]
            review_link = "https://www.flipkart.com" + box1.div.div.a['href']
            reviewRes = requests.get(review_link)
            review_html = bs(reviewRes.text, "html.parser")
            commentboxes = review_html.find_all('div', {'class': "_1AtVbE col-12-12"})

            table = db[searchString]
            reviews = []

            for commentbox in commentboxes:
                name = commentbox.div.div.find_all('p', {'class': '_2sc7ZR _2V5EHH'})[0].text
                rating = commentbox.div.div.div.div.text
                commentHead = commentbox.div.div.div.p.text
                comtag = commentbox.div.div.find_all('div', {'class': ''})
                custComment = comtag[0].div.text
                mydict = {"Product": searchString, "Name": name, "Rating": rating, "CommentHead": commentHead,
                          "Comment": custComment}  # saving that detail to a dictionary
                x = table.insert_one(
                    mydict)  # insertig the dictionary containing the rview comments to the collection
                reviews.append(mydict)  # appending the comments to the review list
            return render_template('results.html', reviews=reviews)
    else:
        return render_template('index.html')

if __name__ == "__main__":
    app.run(port=8000, debug=True)


