import psycopg2
import psycopg2.extras  # We'll need this to convert SQL responses into dictionaries
import json
from flask import Flask, current_app, jsonify
from flask import request


def get_db_connection():
  try:
    conn = psycopg2.connect("user=postgres password=Sigmalabs123 host=database-4.ckpayodailen.eu-west-2.rds.amazonaws.com")
    return conn
  except:
    print("Error connecting to database.")

conn = get_db_connection()


def query_cursor_stories(query, parameters=()):
  #if there is a connection...
    if conn != None:
      #create a cursor -> allows to execute SQL queries -> every-time an endpoint is called
      #opens a tunnel where you can execute queries
      #1 cursor per end point
      
      #the parameters here will ensure data is returned in a nice format
      with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as curs:
          try:
            #executes the query, stores the result in the cursor
              curs.execute(query, parameters)
              #fetchall() will fetch the data the cursor has found
              data = curs.fetchall()
              if len(data) == 0:
                return {"error": "Not Found", "code": 404}
              else:
                data_dic = {'stories': data,"success": 200, "total-stories": len(data)}
                return jsonify(data_dic), 200
          except:
              return "Unable to action this request", 400
    else:
      return "Error Connecting to Database", 500

    
def query_cursor_vote(query, parameters=()):
    if conn != None:
      with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as curs:
          try:
              curs.execute(query, (parameters,))
              conn.commit()
              curs.close()
              return ''
          except:
              return "Unable to action this request", 400
    else:
      return "Error Connecting to Database", 500


app = Flask(__name__)


@app.route("/", methods=["GET"])
def index():
    return current_app.send_static_file("index.html")

@app.route("/search", methods=["GET"])
def tag_search():
  matches = []
  if conn != None:
  
    try:
      input = request.args
      print(input)
      input_dict = dict(input)
      input_dict_values = list(input_dict.values())[0].split(',')
    except:
      return "Unable to action this request", 400

    if conn != None:
      try:
        curs = conn.cursor()
        curs.execute("SELECT title, url, description FROM stories JOIN metadata ON metadata.story_id = stories.id JOIN tags ON tags.id = metadata.tag_id;")
        data = curs.fetchall()
        conn.commit()
      except:
        return "Unable to action this request", 400

    for j in range(len(input_dict_values)):
      for i in range(len(data)):
          if data[i][2].lower() == (input_dict_values[j].lower()):
            matches.append({"Title": data[i][0], "URL": data[i][1], "Tag": data[i][2]})

  matches = {"stories": matches}
  return matches


@app.route("/stories", methods=["GET"])
def stories():
  #setting up query to query from database(SQL query)
    # query = "SELECT *, CASE WHEN score < 0 THEN 0 END duration FROM total_scores ORDER BY score DESC;"
    query = "SELECT stories.*, SUM(CASE direction WHEN 'up' THEN 1 WHEN 'down' THEN -1 ELSE 0 END) AS score FROM stories LEFT JOIN votes ON votes.story_id = stories.id GROUP BY stories.id;"
    return query_cursor_stories(query)
    
@app.route("/stories/<int:id>/votes", methods=['POST'])
def votes(id):
  if request.method == 'POST':
    data = request.json
  if data['direction'] == 'up':
    query = "INSERT INTO votes (direction, created_at, updated_at, story_id) VALUES ('up', current_timestamp, current_timestamp, %s);"
    return query_cursor_vote(query, id)
  elif data['direction'] == 'down':
    query = "INSERT INTO votes (direction, created_at, updated_at, story_id) VALUES ('down', current_timestamp, current_timestamp, %s);"
    return query_cursor_vote(query, id)


# @app.route("/search/tag", methods = ['GET'])
# def search_stories():
#   #make this request into a string. Into a list, then access the value and the first index will provide string of what is typed in
#   data = list(request.json.values())[0]
#   return data




if __name__=='__main__':
        app.run(debug=True,host='0.0.0.0', port = 5000)