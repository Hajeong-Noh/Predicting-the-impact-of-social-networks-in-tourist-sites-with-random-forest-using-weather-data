import requests
from datetime import datetime
import xlwt
import xlrd
import time
import os

# Get current documents
arr = next(os.walk('.'))[2]


last_date = '2013-01-01'

book = xlrd.open_workbook("places in Como.xlsx")
first_sheet = book.sheet_by_index(0)
places = []

for i in range(1,106):
    places.append([first_sheet.row_values(i)[2],
                   first_sheet.row_values(i)[6]])

print(places)
# Filter places with no URL
places = list(filter( lambda x: x[1] != "" and x[1] != "NA", places))

# change idd
places = list(map( lambda x: [x[0],int(x[1].split("/")[5])] , places))

# Filter documents already readed
places = list(filter( lambda x: (str(x[0]) + ".xls" ) not in arr, places))
print(places)



# check for every location
# Como
#idd = 215032588
#first = 60
#after = 1652252279769906829
#query_id = 17865274345132052

# Duomo
# The idd is the only thing that changes
#idd = 220988587
#first = 60
#after = 1652252279769906829
#query_id = 17865274345132052



# Prepare the workbook

""" TODO:
AUTO:
1 - Read document, create a filtered list with [[idd, name],..] with name does't already a document
2 - Run Order_1
"""

# old array is the older array and new array is req['edges']
def getNodes(old_array = [], new_array = []):
    for element in new_array:
        old_array.append({
            'shortcode': element["node"]['shortcode'],
            'date': datetime.utcfromtimestamp(float(element['node']['taken_at_timestamp'])).strftime("%Y-%m-%d"),
            'hour': datetime.utcfromtimestamp(float(element['node']['taken_at_timestamp'])).strftime("%H:%M:%S"),
            'likes': element['node']['edge_liked_by']['count'],
            'video': element['node']['is_video']
        })

def createRequest(idd, query_id="17865274345132052", first="60", after="1652252279769906829"):
    variables = "{" + "\"id\":\"{0}\",\"first\":{1},\"after\":\"{2}\"".format(idd, first, after) + "}"
    request_pre = "https://www.instagram.com/graphql/query/?query_id={0}&variables={1}".format(query_id, variables)
    req = requests.get(request_pre).json()
    if req["status"] == 'fail':
        print("we had an error", after)
        print(req)
    return(req['data']['location'])


def getData(idd):
    # for the excel

    # the array with all the information
    info = []

    # create the request from location
    # default values
    req = createRequest(idd=idd)

    # global info
    location = req["name"]
    lat, lng = req["lat"], req["lng"]

    # boolean that shows if there's a next page and it's a boolean
    next_page = req["edge_location_to_media"]['page_info']["has_next_page"]

    # get next cursor if there a follor page
    if next_page:
        next_cursor = req["edge_location_to_media"]['page_info']["end_cursor"]
    else:
        next_cursor = ""

    # add the current information
    new_info = req["edge_location_to_media"]['edges']
    getNodes(info, new_info)

    #TODO: add limiter  number of pictures
    while next_page and len(info) and (last_date < info[-1]['date']):
        req = createRequest(idd, after=next_cursor)
        try:
            next_page = req["edge_location_to_media"]['page_info']["has_next_page"]
        except:
            print( req["edge_location_to_media"]['page_info']["end_cursor"])
            next_page = ""
        if type(next_page) == bool and next_cursor:
            next_cursor = req["edge_location_to_media"]['page_info']["end_cursor"]
        else:
            next_cursor = ""
        new_info = req["edge_location_to_media"]['edges']
        time.sleep(8)
        getNodes(info, new_info)
        print(info[-1]['date'], len(info))
    return location, lat, lng, info


def writeDocument(idd, name):
    var = getData(idd)
    location = var[0]
    lat, lng = var[1], var[2]
    info = var[3]
    print("info" + "\n", var[3], "\n", len(var[3]))
    book = xlwt.Workbook(encoding="utf-8")
    sheet1 = book.add_sheet("Sheet 1")
    sheet1.write(0, 0 ,"Name Location")
    sheet1.write(0, 1 ,"lat")
    sheet1.write(0, 2 ,"long")
    sheet1.write(0, 3 ,"id")
    sheet1.write(0, 4 ,"date")
    sheet1.write(0, 5 ,"hour")
    sheet1.write(0, 6 ,"likes")
    sheet1.write(0, 7 ,"video")
    for col, val in enumerate(info):
                sheet1.write(col + 1, 0 , location)
                sheet1.write(col + 1, 1, lat)
                sheet1.write(col + 1, 2, lng)
                sheet1.write(col + 1, 3, val['shortcode'])
                sheet1.write(col + 1, 4, val['date'])
                sheet1.write(col + 1, 5, val['hour'])
                sheet1.write(col + 1, 6, val["likes"])
                sheet1.write(col + 1, 7, str(val["video"]))
    book.save(str(name) + ".xls")


for place in places:
    print(place)
    writeDocument(place[1], place[0])
