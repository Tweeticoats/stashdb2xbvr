import os
import requests
import json
import datetime
import re


headers = {
    "Accept-Encoding": "gzip, deflate, br",
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Connection": "keep-alive",
    "DNT": "1"
}
api_url='https://stashdb.org/graphql'

if os.getenv('API_KEY'):
    headers['ApiKey']=os.getenv('API_KEY')


def __callGraphQL(query, variables=None):
    json = {}
    json['query'] = query
    if variables != None:
        json['variables'] = variables

    # handle cookies
    response = requests.post(api_url, json=json, headers=headers)

    if response.status_code == 200:
        result = response.json()
        if result.get("error", None):
            for error in result["error"]["errors"]:
                raise Exception("GraphQL error: {}".format(error))
        if result.get("data", None):
            return result.get("data")
    else:
        raise Exception(
            "GraphQL query failed:{} - {}. Query: {}. Variables: {}".format(response.status_code, response.content,
                                                                            query, variables))


def getScenes(studio_id,page=1,per_page=100):
    query="""query  queryScenes($input: SceneQueryInput!) {
  queryScenes(input: $input) {
    count
   scenes{
    id
    title
    details
    date
    urls{
      url
    }
    studio{
      id
      name
      urls{
        url
      }
    }
    tags{
      id
      name
    }
    images{
      id
      url
      width
      height
    }
    performers{
      performer{
        name
        id
      }
    }
    duration
    code
  }
  }
}"""

    variables={
        "input": {
            "studios": {
                "modifier": "EQUALS",
                "value": [studio_id]
            },
            "page": page,
            "per_page": per_page,
            "sort": "DATE"
        }
    }
    result = __callGraphQL(query, variables)
    return result


def generateJson(studio_id):
    data = {}
    data["timestamp"] = datetime.datetime.now().isoformat() + "Z"
    data["bundleVersion"] = "1"
    res=[]
    scenes_list=[]
    page=1
    per_page=100
    res=getScenes(studio_id,page,per_page)
    index=1
    if res is not None:
        while  (page-1)*per_page < res['queryScenes']['count']:
            print("Processing... "+str((page-1)*per_page)+ "-"+str(page*per_page)+"  " +str(res['queryScenes']['count']))
            for s in res['queryScenes']['scenes']:
                index = index + 1
                r = {}
                r["_id"] = str(index)
                r["scene_id"] = s["id"]
                r["scene_type"] = "VR"
                r["title"] = s["title"]
                if "studio" in s:
                    r["studio"] = s["studio"]["name"]
                if s["images"]:
                    if len(s["images"]):
                        r["covers"] = [s["images"][0]["url"]]
                    r["gallery"] = [x["url"] for x in s["images"]]
                else:
                    r["gallery"] = None
#                r["gallery"] = None
                tags = []
                if "tags" in s:
                    for t in s["tags"]:
                        tags.append(t["name"])
                r["tags"] = tags

                performer = []
                if "performers" in s:
                    for t in s["performers"]:
                        performer.append(t["performer"]["name"])
                r["cast"] = performer
#                path = s["path"][s["path"].rindex('/') + 1:]

                r["synopsis"] = s["details"]
                r["released"] = s["date"]



                for url in s["urls"]:
                    site_url=None
                    # check if the url matches the site url to filter out other links like indexx or iafd etc
                    if "urls" in s["studio"]:
                        for u in s["studio"]["urls"]:
                            if url["url"].startswith(u["url"]):
                                r["homepage_url"]=url["url"]
                    reg=re.search('vrh(\d+)',url["url"])
                    if reg:
                        id=reg.group()[3:]
                        r["_id"] = 'vrhush-'+id
                        r["scene_id"] = id







#                r["homepage_url"] = s["url"]
                print(r["_id"]+" "+r["scene_id"]+" "+r["released"])
                scenes_list.append(r)

            page=page+1
            res = getScenes(studio_id, page, per_page)
            print("loop")

#    data["scenes"] = sorted(scenes_list, key=lambda d: d['scene_id'])
    data["scenes"] = scenes_list
    return data


if __name__ == '__main__':
    id='c85a3d13-c1b9-48d0-986e-3bfceaf0afe5'
    res=generateJson(id)
    print(res)
    file=id+'.json'

    with open(file, 'w') as outfile:
        json.dump(res, outfile,sort_keys=True)
