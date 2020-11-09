from flask import Flask, request, jsonify, render_template
import pickle
from heapq import nlargest

#from flask_json import json_response


app = Flask(__name__)
model = pickle.load(open('C:/Users/saurabh/Desktop/model_KG/sim_final.pkl','rb'))
#df    = pickle.load(open('C:/Users/saurabh/Desktop/model_KG/df_final.pkl','rb'))
#df = pd.read_pickle('C:/Users/saurabh/Desktop/model_KG/df_final.pkl')
#df = df.filter(['Details'])
#dataframe= pd.read_json("Filtered01.json")
#df = pd.read_json(dataframe['structuredLayout'].to_json(), orient="index")
#df['Details']=df.Details.astype(str)

def find_similarity_final(key):
    key = str(key)
    if key in model:
        top3 = nlargest(4,model.get(key), key=model.get(key).__getitem__)
        return top3[1:]
    else:
        return 'ID not exist'     
        


@app.route('/')
def home():
    return render_template('index.html')
    


@app.route('/results',methods=['POST','GET'])
def results():
    #Parse received JSON request
    if request.method=='POST':
     user_input = request.form
     for key,val in user_input.items():
         res= val
     res = int(res)
     
     #Generate recommendation
     recommended_candidate = find_similarity_final(res)
     #recommended_candidate_details = [print(df[df['Details'] == i]) for i in recommended_candidate]
     return jsonify(recommended_candidate)
    
if __name__ == "__main__":
    app.run(debug=True)




