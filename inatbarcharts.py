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

header = {
    "User-Agent": "Checklistinator: iNat Bar Chart(https://inatbarcharts.streamlit.app/; iNat username: ospreyj; joshua.lu.johnson@gmail.com)"
}

st.title("iNat Bar Charts")
st.write("An app that will provide bar charts for the taxa and location of your choosing, like eBird does for birds")	
st.write("You can also hide taxa on your life list, or sort by certain months")

dfs = []

yes = st.text_input("Enter a taxon: ")

col1, col2, col3 = st.columns([1,2,2])

with col1:
	Numberofr = st.text_input("How many results: ", "10")
	Numberofr = int(Numberofr)

Ranks = ["Species", "Genus", "Family", "Order", "Class", "...", "Complex", "Tribe", "Subgenus", "Subfamily", "Superfamily", "Suborder", "Superorder"]

with col2:
	Rank = st.selectbox("What rank I am looking for: ", options = Ranks)
	rank = Rank.lower()

monthlist = ["Year-round", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]


with col3:
	usermonth = st.selectbox("Sort by frequency in: ", options = monthlist)

if rank == "species":
	researchgrade = st.checkbox("Research-grade observations only?")
else:
	researchgrade = False

personallists = ["---", "Life List (Worldwide)", "Life List (selected place)", "Year List (Worldwide)", "Year List (selected place)", "Life List for selected month (all years)", "Life List for selected month (this year)", "Life List for current month (all years)", "Life List for current month (this year)"]

lifelist = st.selectbox("Hide taxa on: ", options = personallists)
if lifelist != '---':
	username = st.text_input("Enter your iNaturalist username:")


query = st.text_input("Enter a place (the format for a state is [State, Country code] and for a county is [County, Country code, State code]): ", placeholder="Examples: Colorado, US; Montgomery, US, MD")


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

if Rank == "...":
	st.write("C'mon now, \"...\" was clearly just to separate the major ranks from the minor ones")
	st.stop()

try:
	res = requests.get(f"https://api.inaturalist.org/v2/taxa/autocomplete?q={yes}&fields=name%2Cpreferred_common_name%2Crank", headers=header)
	if res.status_code != 200:
		st.write(f"Error: {res.status_code}")
	results = res.json().get("results", [])
	taxon = results[0]
except:
	st.write("Couldn't find that taxon")
	st.stop()
try:
	our_name = taxon['preferred_common_name']
except:
	our_name = taxon['name']
placeholdertaxon = st.empty()
placeholdertaxon.write(f"Selected taxon: {our_name}")

try:
	res_place = requests.get(f"https://api.inaturalist.org/v2/places?q={query}&order_by=area&fields=display_name", headers=header)
	if res_place.status_code != 200:
		st.write(f"Error: {res.status_code}")
	results_place = res_place.json().get("results", [])
	place = results_place[0]
	placename = place['display_name']
except:
	st.write("Couldn't find that place")
	st.stop()
placeholderplace = st.empty()
placeholderplace.write(f"Selected place: {placename}")


our_id = taxon['id']
our_place = place['id']

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

if usermonth != "Year-round":
	requestedmonth = datetime.strptime(usermonth, "%B").month
	if researchgrade:
		firsttry = requests.get(f'https://api.inaturalist.org/v1/observations/species_counts?place_id={our_place}&rank={rank}&taxon_id={our_id}&quality_grade=research&month={requestedmonth}&page=1&order=desc&fields=preferred_common_name')
	else:
		firsttry = requests.get(f'https://api.inaturalist.org/v1/observations/species_counts?place_id={our_place}&rank={rank}&taxon_id={our_id}&quality_grade=needs_id,research&month={requestedmonth}&page=1&order=desc&fields=preferred_common_name')
else:
	if researchgrade:
		firsttry = requests.get(f'https://api.inaturalist.org/v1/observations/species_counts?place_id={our_place}&rank={rank}&taxon_id={our_id}&quality_grade=research&page=1&order=desc&fields=preferred_common_name')
	else:
		firsttry = requests.get(f'https://api.inaturalist.org/v1/observations/species_counts?place_id={our_place}&rank={rank}&taxon_id={our_id}&quality_grade=needs_id,research&page=1&order=desc&fields=preferred_common_name')

totalresults = firsttry.json()['results']

if len(totalresults) == 0:
	st.write(f"No instances of {our_name} in {placename}")
	st.stop()

if lifelist != "---":
	time.sleep(1)

user_lifelist = []

try:
	if lifelist == "Life List (Worldwide)":
		secondcheck = requests.get(f'https://api.inaturalist.org/v2/observations/taxonomy?user_id={username}&taxon_id={our_id}')
	elif lifelist == "Life List (selected place)":
		secondcheck = requests.get(f'https://api.inaturalist.org/v2/observations/taxonomy?place_id={our_place}&user_id={username}&taxon_id={our_id}')
	elif lifelist == "Year List (Worldwide)":
		secondcheck = requests.get(f'https://api.inaturalist.org/v2/observations/taxonomy?user_id={username}&taxon_id={our_id}&year={today.year}')
	elif lifelist == "Year List (selected place)":
		secondcheck = requests.get(f'https://api.inaturalist.org/v2/observations/taxonomy?place_id={our_place}&user_id={username}&taxon_id={our_id}&year={today.year}')
	elif lifelist == "Life List for selected month (all years)":
		secondcheck = requests.get(f'https://api.inaturalist.org/v2/observations/taxonomy?user_id={username}&taxon_id={our_id}&month={requestedmonth}')
	elif lifelist == "Life List for selected month (this year)":
		secondcheck = requests.get(f'https://api.inaturalist.org/v2/observations/taxonomy?&user_id={username}&taxon_id={our_id}&year={today.year}&month={requestedmonth}')
	elif lifelist == "Life List for current month (all years)":
			secondcheck = requests.get(f'https://api.inaturalist.org/v2/observations/taxonomy?user_id={username}&taxon_id={our_id}&month={today.month}')
	elif lifelist == "Life List for current month (this year)":
			secondcheck = requests.get(f'https://api.inaturalist.org/v2/observations/taxonomy?&user_id={username}&taxon_id={our_id}&year={today.year}&month={today.month}')

	lifemask = secondcheck.json()['results']
	for x in range(0, len(lifemask)):
		user_lifelist.append(lifemask[x]['id'])

except:
	user_lifelist = []



#time.sleep(5)
taxaids = []
names = []

#CALC = """
#Starting...
#"""




#def stream_data_ca():
#    for word in list(CALC):
#        yield word + " "
#        time.sleep(0.1)

#attempt = st.write_stream(stream_data_ca())


for x in range(0, len(totalresults)):
	if len(names) == Numberofr:
		break
	if totalresults[x]['taxon']['rank'] != rank:
		continue
	if totalresults[x]['taxon']['id'] in user_lifelist:
		continue
	try:
		taxaids.append(totalresults[x]['taxon']['id'])
		if rank == "species":
			try:
				taxa = (totalresults[x]['taxon']['preferred_common_name'])
				names.append(taxa)
			except:
				taxa = (totalresults[x]['taxon']['name'])
				names.append(taxa)
		else:	
			taxa = (totalresults[x]['taxon']['name'])
			names.append(taxa)
	except:
		continue

esttime = min(Numberofr, len(names))
taxadict = dict(zip(taxaids, names))
#time.sleep(15)

observation_df_large = pl.DataFrame()

placeholder = st.empty()

numdone = 1



for taxonid in taxaids:
	placeholder.write(f"{numdone} finished out of {esttime}")
	time.sleep(1)
	if researchgrade:
		response = requests.get(f'https://api.inaturalist.org/v2/observations/histogram?place_id={our_place}&taxon_id={taxonid}&quality_grade=research&order=desc&fields=species_guess%2Cobserved_on&date_field=observed&interval=week_of_year')
	else:
		response = requests.get(f'https://api.inaturalist.org/v2/observations/histogram?place_id={our_place}&taxon_id={taxonid}&quality_grade=needs_id,research&order=desc&fields=species_guess%2Cobserved_on&date_field=observed&interval=week_of_year')
	observations = response.json()['results']['week_of_year']
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
#combined_df = combined_df.sort('rowsum', descending=True)
combined_df = combined_df.drop('rowsum')
ids = combined_df.select(["id"])

url = "https://api.inaturalist.org/v1/taxa/autocomplete"
for x in range(0,ids.height):
	combined_df = combined_df.group_by("id", maintain_order=True).agg(cs.numeric().sum())
	yes = ids[x,0]
	taxa = taxadict[int(yes)]
	combined_df = combined_df.with_columns(id = pl.when(pl.col("id") == yes).then(pl.lit(taxa)).otherwise(pl.col("id")))


combined_df = combined_df.group_by("id", maintain_order=True).agg(cs.numeric().sum())
df = combined_df.head(int(Numberofr))

placeholdertaxon.empty()
placeholderplace.empty()

#st.write(sns.load_dataset(df))

df_max = df.drop("id")
provmax = df_max.select(pl.max_horizontal("*")).max().item()
if provmax is None:
	st.write(f"No instances of {our_name} found in {placename}!")
	st.stop()
elif provmax > 35:
	absolute_max = round(provmax/2)
else:
	absolute_max = round(provmax)

df_pd = df.to_pandas()
df_pd = df_pd.set_index("id")
df_pd = df_pd.dropna(how="all")  # drop rows that are all NaNs

fig, ax = plt.subplots(figsize=(16, esttime))
sns.heatmap(df_pd, cmap="Purples", linewidths=0.2, linecolor='gray', vmax=absolute_max, ax=ax)

ax.set_title(f"Frequency of {our_name} in {placename}", fontsize=15)
ax.set_xlabel("Half-Month", fontsize=15)
ax.set_ylabel("Species", fontsize=15)

positions = [0,5,9,13,18,22,26,31,35,40,44,48]

reallabels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


ylabs = df_pd.index.tolist()
ypos = range(0,len(ylabs))
realypos = []
for pos in ypos:
	realypos.append(pos + 0.5)

ax.set_xticks(positions, rotation=45, ha="right", labels=reallabels, fontsize=15)
ax.set_yticks(realypos, rotation=0, ha="right", labels=ylabs, fontsize=15)
st.pyplot(fig)

figy = esttime*5/3
axes = df_pd.T.plot.line(subplots=True, sharex=True, sharey=True, ylim=(0, absolute_max), legend=False, figsize=(16,figy))
fig2 = axes.flatten()[0].get_figure()
for ax, title in zip(axes.flatten(), ylabs):
  ax.set_title(title, fontsize=15)
  ax.set_xticks(positions, rotation=45, ha="right", labels=reallabels, fontsize=15)
plt.tight_layout()
st.pyplot(fig2)
