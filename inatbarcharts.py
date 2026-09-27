import requests
import polars as pl
import polars.selectors as cs
import datetime
from datetime import date, timedelta
from datetime import datetime
#import seaborn
import calendar
import functools
from functools import reduce
import time
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from dateutil.relativedelta import relativedelta
import streamlit as st
import math
from matplotlib.offsetbox import (OffsetImage, AnnotationBbox)
from matplotlib.cbook import get_sample_data
from PIL import Image
from io import BytesIO
import numpy as np

st.set_page_config(page_title="iNat Bar Charts")
#,layout="wide"


header = {
    "User-Agent": "Checklistinator: iNat Bar Chart(https://inatbarcharts.streamlit.app/; iNat username: ospreyj; joshua.lu.johnson@gmail.com)"
}

if "hiddenq" not in st.session_state:
	st.session_state["hiddenq"] = 0

if "hiddenq_text" not in st.session_state:
	st.session_state["hiddenq_text"] = 0

if "reset_actions" not in st.session_state:
	st.session_state["reset_actions"] = False

def trigger_reset(source):
	st.session_state["reset_actions"] = True
	st.session_state["reset_source"] = source

def update_from_text():
	try:
		st.session_state["hidden_value"] = int(
			st.session_state["hiddenq_text"]
		)
        #st.session_state["reset_actions"] = True
		trigger_reset("update_from_text")
	except ValueError:
		pass

def update_from_slider():
	st.session_state["hidden_value"] = st.session_state['hidden_slider']
    #st.session_state["reset_actions"] = True
	trigger_reset("update_from_slider")


#def max_from_text():
#	st.write("AAAAAAAAAA")
#	st.write(st.session_state["hidden_max"])
#	if st.session_state["refresh"] != "slide":
#		st.session_state["hidden_max"] = int(
#			st.session_state["maxq_text"]
#		)
#		#st.session_state["reset_actions"] = 0
#		st.session_state["refresh"] = "text"
#		st.write(st.session_state["hidden_max"])

#def max_from_slider():
#	st.write("BBBBBBBBB")
#	st.write(st.session_state["hidden_max"])
#	if st.session_state["refresh"] != "text":
#		st.session_state["hidden_max"] = st.session_state['hidden_max_slider']
#		st.session_state["refresh"] = "slide"
#	st.write(st.session_state["hidden_max"])
#	#st.session_state["reset_actions"] = 0

def max_from_text():
	try:
		st.session_state["hidden_max"] = int(
			st.session_state["maxq_text"]
        )
		st.session_state['hidden_max_slider'] = st.session_state["maxq_text"]
	except ValueError:
		pass

def max_from_slider():
	st.session_state["hidden_max"] = st.session_state['hidden_max_slider']
	st.session_state["maxq_text"] = str(st.session_state['hidden_max_slider'])




def reset():
	st.session_state["hidden_value"] = 0
	st.session_state["hiddenq_text"] = str(st.session_state["hidden_value"])
	st.session_state["hidden_slider"] = st.session_state["hidden_value"]
	#st.session_state["reset_actions"] = True
	trigger_reset("reset")
	st.session_state["maxq_text"] = "0"


if "hidden_value" not in st.session_state:
    st.session_state["hidden_value"] = 0

st.session_state["refresh"] = 0

if "hidden_max_slider" not in st.session_state:
    st.session_state["hidden_max_slider"] = 0

if "slider_version" not in st.session_state:
    st.session_state["slider_version"] = 0

if "hidden_slider" not in st.session_state:
    st.session_state["hidden_slider"] = 0

if "hidden_max" not in st.session_state:
    st.session_state["hidden_max"] = 0


#try:
#	hiddenq = st.session_state["slider"]
#except:
#	hiddenq = 0


params = {}

@st.cache_data(show_spinner=False)
def read_iNat_API(url,params:dict,fieldlist:list):
	resultslist = []
	time.sleep(1)
	res = requests.get(url, params=params)
	if res.status_code != 200:
		st.write(f"Error: {res.status_code}")
	if len(fieldlist) == 1:
		results = res.json()[fieldlist[0]]
		return results
	else:
		for field in fieldlist:
			resultslist.append(res.json()[field])
		return resultslist


st.title("iNat Bar Charts")
st.write("An app that will provide bar charts for the taxa and location of your choosing, like eBird does for birds")	
st.write("You can also hide taxa on your life list, or sort by certain months")
st.write("You can show photos, but in my opinion they make the axes look quite stretched")

dfs = []

yes = st.text_input("Enter a taxon: ", on_change=reset)

col1, col2, col3 = st.columns([1,2,2])

with col1:
	Numberofr = st.text_input("How many results: ", "8", on_change=reset)
	Numberofr = int(Numberofr)

Ranks = ["Species", "Genus", "Family", "Order", "Class", "...", "Complex", "Tribe", "Subgenus", "Subfamily", "Superfamily", "Suborder", "Superorder"]

with col2:
	Rank = st.selectbox("What rank I am looking for: ", options = Ranks, on_change=reset)
	rank = Rank.lower()

monthlist = ["Year-round", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]


with col3:
	usermonth = st.selectbox("Sort by frequency in: ", options = monthlist, on_change=reset)

if Rank == "...":
	st.write("C'mon now, \"...\" was clearly just to separate the major ranks from the minor ones")
	st.stop()


with st.expander("Extra Options (Pictures, Research grade, Life list, Annotations)"):

	col1, col2 = st.columns(2)
	with col1:
		picturesq = st.checkbox("Pictures? (1 extra second for every 4 results)")

	if rank == "species":
		with col2:
			researchgrade = st.checkbox("Research-grade observations only?")
	else:
		researchgrade = False

	st.divider()

	personallists = ["---", "Life List (Worldwide)", "Life List (selected place)", "Year List (Worldwide)", "Year List (selected place)", "Life List for selected month (all years)", "Life List for selected month (this year)", "Life List for current month (all years)", "Life List for current month (this year)"]

	lifelist = st.selectbox("Hide taxa on: ", options = personallists, on_change=reset)
	if lifelist != '---':
		username = st.text_input("Enter your iNaturalist username:", on_change=reset)

	st.divider()
	col1, col2 = st.columns(2)

	with col1:
		coarsitylist = ['Week', 'Month']
		coarsityq = st.selectbox("I want results for every: ", options = coarsitylist, on_change=reset)
		if coarsityq == "Week":
			positions = [0,5,9,13,18,22,26,31,35,40,44,48]
		if coarsityq == "Month":
			positions = range(0,12)

	with col2:
		if Rank == "Species":
			nametypeslist = ['Common Names', 'Scientific Names', 'Both Common and Scientific Names']
		else:
			nametypeslist = ['Scientific Names', 'Common Names', 'Both Common and Scientific Names']

		nametypesq = st.selectbox("I would like: ", options = nametypeslist)

	st.divider()


	col1, col2 = st.columns(2)

	annotationslist = ['---', 'Life Stage', 'Sex', 'Flowers and Fruits', 'Leaves', 'Alive or Dead', 'Evidence of Presence']
	annotationsdict = {'Life Stage': 1, 'Sex': 9, 'Flowers and Fruits': 12, 'Leaves': 36, 'Alive or Dead': 17, 'Evidence of Presence': 22}

	with col1:
		annotationsq = st.selectbox("Observations with annotation: ", options = annotationslist, on_change=reset)
	
		if annotationsq == '---':
			annotationsvalues = ['---']
		elif annotationsq == 'Life Stage':
			annotationsvalues = ['---', 'Adult', 'Teneral', 'Pupa', 'Nymph', 'Larva', 'Egg', 'Juvenile', 'Subimago']
			annotationsvaldict = {'Adult': 2, 'Teneral': 3, 'Pupa': 4, 'Nymph': 5, 'Larva': 6, 'Egg': 7, 'Juvenile': 8, 'Subimago': 16}
		elif annotationsq == 'Sex':
			annotationsvalues = ['---', 'Female', 'Male', 'Cannot Be Determined']
			annotationsvaldict = {'Female': 10, 'Male': 11, 'Cannot Be Determined': 20}
		elif annotationsq == 'Flowers and Fruits':
			annotationsvalues = ['---', 'Flowers', 'Fruits or Seeds', 'Flower Buds', 'No Flowers or Fruits']
			annotationsvaldict = {'Flowers': 13, 'Fruits or Seeds': 14, 'Flower Buds': 15, 'No Flowers or Fruits': 21}
		elif annotationsq == 'Leaves':
			annotationsvalues = ['---', 'Breaking Leaf Buds', 'Green Leaves', 'Colored Leaves', 'No Live Leaves']
			annotationsvaldict = {'Breaking Leaf Buds': 37, 'Green Leaves': 38, 'Colored Leaves': 39, 'No Live Leaves': 40}
		elif annotationsq == 'Alive or Dead':
			annotationsvalues = ['---', 'Alive', 'Dead', 'Cannot Be Determined']
			annotationsvaldict = {'Alive': 18, 'Dead': 19, 'Cannot Be Determined': 20}
		elif annotationsq == 'Evidence of Presence':
			annotationsvalues = ['---', 'Feather', 'Organism', 'Scat', 'Track', 'Bone', 'Molt', 'Gall', 'Egg', 'Hair', 'Leafmine', 'Construction']
			annotationsvaldict = {'Feather': 23, 'Organism': 24, 'Scat': 25, 'Track': 26, 'Bone': 27, 'Molt': 28, 'Gall': 29, 'Egg': 30, 'Hair': 31, 'Leafmine': 32, 'Construction': 35}

			
	
	
	with col2:
		annotationsvalueq = st.selectbox("Annotation value: ", options = annotationsvalues, on_change=reset)

	if annotationsq != '---' and annotationsvalueq != '---':
		invertq = st.checkbox("Without this annotation (e.g., if you select \"life stage: adult\" you get all results that are *not* adults)", on_change=reset)
	else:
		invertq = False

	col1, col2 = st.columns(2)
		
	with col1:
		fieldsq = st.text_input("Observations with field: ", on_change=reset)
	with col2:
		fieldsvaluesq = st.text_input("Field value: ", on_change=reset)


query = st.text_input("Enter a place (the format for a state is [State, Country code] and for a county is [County, Country code, State code]): ", placeholder="Examples: Colorado, US; Montgomery, US, MD", on_change=reset)


if not yes:
	st.stop()

if not query:
	st.stop()
		
if not Numberofr:
	st.stop()

if not rank:
	st.stop()

if lifelist != '---' and not username:
	st.stop()

if Numberofr > 30:
	st.write("The maximum number of results is 30")
	st.stop()

if annotationsq != '---' and annotationsvalueq == '---':
	st.stop()

if fieldsq and not fieldsvaluesq:
	st.stop()

try:
	res = read_iNat_API("https://api.inaturalist.org/v2/taxa/autocomplete", {'q': yes, 'fields': "name,preferred_common_name,rank"}, ['results'])
	taxon = res[0]
except:
	st.write("Couldn't find that taxon")
	st.stop()


try:
	res_place = read_iNat_API("https://api.inaturalist.org/v2/places", {'q': query, "fields": "display_name", "order_by": "area"}, ['results']) 
except:
	st.write("Couldn't find that place")
	st.stop()


possibletaxaids =[]
possibletaxacommonnames = []
possibletaxanames = []
possibleplaces = []
possiblenames = []
for taxon in res[0:min(14, len(res))]:
	possibletaxaids.append(taxon['id'])
	possibletaxanames.append(taxon['name'])
	try:
		possibletaxacommonnames.append(taxon['preferred_common_name'])
	except:
		possibletaxacommonnames.append(taxon['name'])

commonnamesdict = dict(zip(possibletaxacommonnames, possibletaxaids))
taxanamedict = dict(zip(possibletaxaids, possibletaxanames))

for place in res_place[0:min(14, len(res_place))]:
	possibleplaces.append(place['id'])
	possiblenames.append(place['display_name'])
placedict = dict(zip(possiblenames, possibleplaces))
with st.expander("Extra selection (if the API chooses the wrong taxon and/or place)"):
	ourcommonname = st.selectbox("Taxon: ", options = possibletaxacommonnames, on_change=reset)
	placename = st.selectbox("Place: ", options = possiblenames, on_change=reset)

our_id = commonnamesdict[ourcommonname]
our_sciencename = taxanamedict[our_id]

if str(ourcommonname) == str(our_sciencename):
	our_name = str(our_sciencename)
else:
	our_name = str(ourcommonname)
	oursceintificname = str(our_sciencename)

placeholdertaxon = st.empty()

try:
	placeholdertaxon.write(f"Selected taxon: {our_name} (*{oursceintificname}*)")
except:
	placeholdertaxon.write(f"*{our_name}*")

placeholderplace = st.empty()
placeholderplace.write(f"Selected place: {placename}")




#our_id = taxon['id']
#our_place = place['id']
our_place = placedict[placename]
try:
	requestedmonth = datetime.strptime(usermonth, "%B").month
except:
	requestedmonth = False
if researchgrade:
	grade = 'research'
else:
	grade = 'needs_id,research'
try:
	term = annotationsdict[annotationsq]
	termv = annotationsvaldict[annotationsvalueq]
except:
	term = False
	termv = False




params['place_id'] = our_place
params['taxon_id'] = our_id
#params['rank'] = rank

if requestedmonth:
	params['month'] = requestedmonth
else:
	pass

params['quality_grade'] = grade

if invertq:
	if term:
		params['term_id'] = term
		params['without_term_value_id'] = termv
	else:
		pass
else:
	if term:
		params['term_id'] = term
		params['term_value_id'] = termv
	else:
		pass

if fieldsq:
	params[f'field:{fieldsq}'] = fieldsvaluesq
else:
	pass





today = date.today()
firstdate = date.today() - relativedelta(years=2)
if 1 <= today.day < 14:
	ourday = "01"
else:
	ourday = "16"
if today.month < 10:
	ourmonth = f"0{str(today.month)}"	
else:
	ourmonth = str(today.month)
date_starts = ['01-01','01-16','02-01','02-16','03-01','03-16','04-01','04-16','05-01','05-16','06-01','06-16','07-01','07-16','08-01','08-16','09-01','09-16','10-01','10-16','11-01','11-16','12-01','12-16']
ourstart = f'{ourmonth}-{ourday}'
dateindex = date_starts.index(ourstart)



firstresults = read_iNat_API('https://api.inaturalist.org/v1/observations/taxonomy', params, ['results'])

if len(firstresults) == 0:
	speciesresults = read_iNat_API('https://api.inaturalist.org/v1/observations/species_counts', {'place_id':our_place, 'rank':'species', 'taxon_id': our_id, 'quality_grade': 'needs_id,research', 'page': 1, 'order': 'desc', 'fields': 'preferred_common_name'}, ['results'])
	if len(speciesresults) == 0:
		st.write(f"No instances of {our_name} in {placename}")
	else:
		st.write(f"No results in that time frame; maybe try some different parameters?")
	st.stop()


user_lifelist = []



if lifelist != '---':
	lifelistparams ={}
	lifelistparams['taxon_id'] = our_id
	if username:
		lifelistparams['user_id'] = username
	if lifelist == "Year List (Worldwide)" or lifelist == "Year List (selected place)" or lifelist == "Life List for selected month (this year)" or lifelist == "Life List for current month (this year)":
		lifelistparams['year'] = today.year
	if lifelist == "Life List (selected place)" or lifelist == "Year List (selected place)":
		lifelistparams['place_id'] = our_place
	if lifelist == "Life List for selected month (all years)" or  lifelist == "Life List for selected month (this year)" :
		lifelistparams['month'] = requestedmonth
	if lifelist == "Life List for current month (all years)" or lifelist == "Life List for current month (this year)":
		lifelistparams['month'] = today.month
	
	lifemask = read_iNat_API(url='https://api.inaturalist.org/v2/observations/taxonomy', params=lifelistparams, fieldlist=['results'])

	for x in range(0, len(lifemask)):
		user_lifelist.append(lifemask[x]['id'])

else:
	user_lifelist = []


#time.sleep(5)
taxaids = []
names = []
photos = []

#CALC = """
#Starting...
#"""

resultstaxa = []
resultscount = []

for x in range(0, len(firstresults)):
	try:
		if firstresults[x]['rank'] != rank:
			continue
	except:
		continue
	if firstresults[x]['id'] in user_lifelist:
		continue
	resultstaxa.append(firstresults[x]['id'])
	resultscount.append(firstresults[x]['descendant_obs_count'])

firstdf = pl.DataFrame({
    "id": resultstaxa,
    "count": resultscount
})

firstdf = firstdf.sort(pl.col("count"), descending=True)
numcouldhide = max (((firstdf.height) - (1)), 0)
if st.session_state["hidden_value"] >= firstdf.height:
	st.session_state["hidden_value"] = 0
hiddennum = st.session_state["hidden_value"]
firstdf = firstdf[(hiddennum):(hiddennum + Numberofr)]
#st.write(firstdf)
#firstdf.head(Numberofr)
ourresults = firstdf.get_column("id").to_list()

placeeholdersearch = st.empty()
placeeholdersearch.write(f"Finding the most common taxa at the rank of {rank}...")

page = 1
while page < 60:
	if len(names) >= Numberofr:
		break
	if len(names) >= len(ourresults):
		break

	if page > 8:
		for taxon_id in ourresults:
			if taxon_id in taxaids:
				continue
			totres = read_iNat_API(url=('https://api.inaturalist.org/v1/taxa'), params={'place_id':our_place, 'rank':rank, 'taxon_id':taxon_id, 'page':1, 'per_page':200, 'order':'desc'}, fieldlist=['results', 'total_results', 'page'])
			totalresults = totres[0]
			resultsnumber = totres[1]
			pagenumber = totres[2]
			for x in range(0, len(totalresults)):
				if len(names) == Numberofr:
					break
				if totalresults[x]['id'] not in ourresults:
					continue
				if totalresults[x]['rank'] != rank:
					continue
				if totalresults[x]['id'] in user_lifelist:
					continue
				try:
					taxaids.append(totalresults[x]['id'])
					if rank == "species":
						try:
							taxa = (totalresults[x]['preferred_common_name'])
							names.append(taxa)
						except:
							taxa = (totalresults[x]['name'])
							names.append(taxa)
					else:	
						taxa = (totalresults[x]['name'])
						names.append(taxa)
				except:
					continue
				try:
					photos.append(totalresults[x]['default_photo']['medium_url'])
				except:
					photos.append("https://inaturalist-open-data.s3.amazonaws.com/photos/2/square.jpg")

	totres = read_iNat_API(url=('https://api.inaturalist.org/v1/taxa'), params={'place_id':our_place, 'rank':rank, 'taxon_id':our_id, 'page':page, 'per_page':500, 'order':'desc'}, fieldlist=['results', 'total_results', 'page'])


	totalresults = totres[0]
	resultsnumber = totres[1]
	pagenumber = totres[2]
	#st.write(totalresults[1:10])

	for x in range(0, len(totalresults)):
		if len(names) == Numberofr:
			break
		if totalresults[x]['id'] not in ourresults:
			continue
		if totalresults[x]['rank'] != rank:
			continue
		if totalresults[x]['id'] in user_lifelist:
			continue
		try:
			taxaids.append(totalresults[x]['id'])
			if nametypesq == "Common Names":
				try:
					taxa = (totalresults[x]['preferred_common_name'])
					names.append(taxa)
				except:
					clean_name = totalresults[x]['name'].replace(" ", r"\ ")
					taxa = r"$\it{" + clean_name + "}$"
					names.append(taxa)
			elif nametypesq == "Scientific Names":
				clean_name = totalresults[x]['name'].replace(" ", r"\ ")	
				taxa = r"$\it{" + clean_name + "}$"
				names.append(taxa)
			elif nametypesq == "Both Common and Scientific Names":	
				try:
					comnam = totalresults[x]['preferred_common_name']
					clean_name = totalresults[x]['name'].replace(" ", r"\ ")
					nam = r"$\it{" + clean_name + "}$"
					#nam = totalresults[x]['name']
					taxa = (f"{comnam}\n({nam})")
					names.append(taxa)
				except:
					clean_name = totalresults[x]['name'].replace(" ", r"\ ")
					taxa = r"$\it{" + clean_name + "}$"
					names.append(taxa)
		except:
			continue
		try:
			photos.append(totalresults[x]['default_photo']['medium_url'])
		except:
			photos.append("https://inaturalist-open-data.s3.amazonaws.com/photos/2/square.jpg")
	if page >= (resultsnumber/pagenumber):
		break
	page += 1
	

esttime = min(Numberofr, len(names))
taxadict = dict(zip(taxaids, names))
photodict = dict(zip(taxaids, photos))
observation_df_large = pl.DataFrame()

placeeholdersearch.empty()
placeholder = st.empty()

numdone = 1

histoparams = {}

histoparams['place_id'] = our_place
histoparams['quality_grade'] = grade

if invertq:
	if term:
		histoparams['term_id'] = term
		histoparams['without_term_value_id'] = termv
	else:
		pass
else:
	if term:
		histoparams['term_id'] = term
		histoparams['term_value_id'] = termv
	else:
		pass

if fieldsq:
	histoparams[f'field:{fieldsq}'] = fieldsvaluesq
else:
	pass

if coarsityq == 'Week':
	histoparams['interval'] = 'week_of_year'
elif coarsityq == 'Month':
	histoparams['interval'] = 'month_of_year'


for taxonid in taxaids:
	histoparams['taxon_id'] = taxonid
	placeholder.write(f"{numdone} finished out of {esttime}")
	response = read_iNat_API(url='https://api.inaturalist.org/v2/observations/histogram', params=histoparams, fieldlist=['results'])
	if coarsityq == 'Week':
		observations = response['week_of_year']
	elif coarsityq == 'Month':
		observations = response['month_of_year']
	observation_df = pl.DataFrame(observations, strict=False, infer_schema_length=None)
	idcol = pl.Series("id", [taxonid])
	observation_df.insert_column(0, idcol)
	observation_df_large = pl.concat([observation_df_large, observation_df])
	placeholder.empty()
	numdone += 1


combined_df = observation_df_large
ids = combined_df.select(["id"])


successes = 0
combined_df = combined_df.with_columns(pl.col("id").cast(pl.String))


combined_df = combined_df.with_columns(rowsum = pl.sum_horizontal(cs.numeric()))
combined_df = combined_df.sort('rowsum', descending=True)


combined_df = combined_df.sort(pl.col("id").replace(ourresults, range(len(ourresults))))

combined_df = combined_df.drop('rowsum')
combined_df = combined_df.head(int(Numberofr))

ids = combined_df.select(["id"])

actual_photos = []

@st.cache_data(show_spinner=False)
def getphoto(photourl):
	time.sleep(0.25)
	photo = requests.get(photourl)
	image_graph = Image.open(BytesIO(photo.content))
	return image_graph

url = "https://api.inaturalist.org/v1/taxa/autocomplete"
for x in range(0,ids.height):
	time.sleep(0.25)
	combined_df = combined_df.group_by("id", maintain_order=True).agg(cs.numeric().sum())
	yes = ids[x,0]
	taxa = taxadict[int(yes)]
	photourl = photodict[int(yes)]
	ourphoto = getphoto(photourl)
	actual_photos.append(ourphoto)
	combined_df = combined_df.with_columns(id = pl.when(pl.col("id") == yes).then(pl.lit(taxa)).otherwise(pl.col("id")))


combined_df = combined_df.group_by("id", maintain_order=True).agg(cs.numeric().sum())

#st.write(sns.load_dataset(df))

df_max = combined_df.drop("id")
provmax = df_max.select(pl.max_horizontal("*")).max().item()
provmin = max((df_max.select(pl.min_horizontal("*")).min().item()), 1)
if provmax is None:
	st.write(f"No instances of {our_name} found in {placename}!")
	st.stop()
elif provmax > 35:
	absolute_max = round(provmax/2)
else:
	absolute_max = round(provmax)

provmax = max(provmax,1)

if "absolute_max" not in st.session_state:
    st.session_state["absolute_max"] = 0

st.session_state["absolute_max"] = absolute_max

if "maxq_text" not in st.session_state:
    st.session_state["maxq_text"] = absolute_max

if "maxq_text_2" not in st.session_state:
    st.session_state["maxq_text_2"] = absolute_max

if st.session_state["hidden_max"] == 0:
    st.session_state["hidden_max"] = absolute_max

if st.session_state["reset_actions"]:
	st.session_state["hidden_max"] = absolute_max
	st.session_state["maxq_text"] = str(st.session_state["hidden_max"])
	st.session_state["hidden_slider"] = int(st.session_state["hidden_value"])
	st.session_state["hiddenq_text"] = str(st.session_state["hidden_value"])
	st.session_state["reset_actions"] = False

df_pd = combined_df.to_pandas()
df_pd = df_pd.set_index("id")
df_pd = df_pd.dropna(how="all")  # drop rows that are all NaNs

with st.expander("Graph sliders"):
	st.write("Note: Editing this box before both graphs have been printed messes Streamlit up")
	st.write("You'll know both graphs are done when \"selected taxon\" and \"selected place\" disappear")
	col1, col2 = st.columns([2,4])
	with col1:
		maxqtex = st.text_input("Maximum value:", st.session_state["maxq_text"], key="maxq_text", on_change=max_from_text)
		#maxqtex = int(maxqtex)

		#currentlyhidden = int(st.session_state["slider"])
		if numcouldhide > 0:
			st.text_input("Hide top ___ results:", st.session_state["hidden_value"], key="hiddenq_text", on_change=update_from_text)

	with col2:
		if provmax != 1:
			maxq = st.slider("Maximum value:", provmin, provmax, (int(st.session_state["hidden_max"])), key="hidden_max_slider", on_change=max_from_slider)
		else:
			maxq = 1

		if numcouldhide > 0:
			hiddenq = st.slider("Hide top ___ results:", 0, numcouldhide, st.session_state["hidden_value"], key="hidden_slider", on_change=update_from_slider)
		#hiddenq = st.slider("Hide top ___ results:", 0, numcouldhide, hiddennum, key="hiddenq")
	if numcouldhide > 0:
		st.session_state["hidden_value"] = hiddenq
	else:
		st.session_state["hidden_value"] = 0

st.session_state["reset_actions"] = 0

if picturesq:
	fig, ax = plt.subplots(figsize=(16, (esttime*2.5)))
else:
	fig, ax = plt.subplots(figsize=(16, esttime))
sns.heatmap(df_pd, cmap="Purples", linewidths=0.2, linecolor='gray', vmax=int(st.session_state["hidden_max"]), ax=ax)

if usermonth != "Year-round":
	ax.set_title(f"Frequency of {our_name} in {placename} in {usermonth}", fontsize=15)
else:
	ax.set_title(f"Frequency of {our_name} in {placename}", fontsize=15)

ax.set_xlabel("Week", fontsize=15)
ax.set_ylabel(f"{Rank}", fontsize=15)

reallabels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


ylabs = df_pd.index.tolist()
ypos = range(0,len(ylabs))
realypos = []
for pos in ypos:
	realypos.append(pos + 0.5)

ax.set_xticks(positions, rotation=45, ha="right", labels=reallabels, fontsize=15)
ax.set_yticks(realypos, rotation=0, ha="right", labels=ylabs, fontsize=15)
if picturesq:
	if coarsityq == "Week":
		ax.set_xlim(0, 63)
		for y in range(1, len(actual_photos) + 1):
			photograph = actual_photos[y-1]
			img_array = np.array(photograph)
			imagebox = OffsetImage(img_array,zoom=0.25)
			imagebox.image.axes = ax
			ab = AnnotationBbox(imagebox, [60, y-0.5], frameon=False)
			ax.add_artist(ab)
	if coarsityq == "Month":
			ax.set_xlim(0, 16)
			for y in range(1, len(actual_photos) + 1):
				photograph = actual_photos[y-1]
				img_array = np.array(photograph)
				imagebox = OffsetImage(img_array,zoom=0.25)
				imagebox.image.axes = ax
				ab = AnnotationBbox(imagebox, [14, y-0.5], frameon=False)
				ax.add_artist(ab)
st.pyplot(fig)

if picturesq:
	figy = esttime*2.5
else:
	figy = esttime*5/3
axes = df_pd.T.plot.line(subplots=True, sharex=True, sharey=True, ylim=(0, int(st.session_state["hidden_max"])), legend=False, figsize=(16,figy))
fig2 = axes.flatten()[0].get_figure()
for y, (ax, title) in enumerate(zip(axes.flatten(), ylabs)):
  ax.set_title(title, fontsize=15)
  ax.set_xticks(positions, rotation=45, ha="right", labels=reallabels, fontsize=15)
  if picturesq:
    if coarsityq == "Week":
      ax.set_xlim(-10, 63)
      photograph = actual_photos[y]
      img_array = np.array(photograph)
      imagebox = OffsetImage(img_array,zoom=0.25)
      imagebox.image.axes = ax
      ab = AnnotationBbox(imagebox, [-5, int(st.session_state["hidden_max"])/2], frameon=False)
      ax.add_artist(ab)
    if coarsityq == "Month":
      ax.set_xlim(-2, 12)
      photograph = actual_photos[y]
      img_array = np.array(photograph)
      imagebox = OffsetImage(img_array,zoom=0.25)
      imagebox.image.axes = ax
      ab = AnnotationBbox(imagebox, [-1, int(st.session_state["hidden_max"])/2], frameon=False)
      ax.add_artist(ab)
plt.tight_layout()
st.pyplot(fig2)

placeholdertaxon.empty()
placeholderplace.empty()
