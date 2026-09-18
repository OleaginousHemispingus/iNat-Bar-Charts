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

all_obs = []

def daterange(start_date, end_date):
	current = start_date
	while current < end_date:
		_, last_day = calendar.monthrange(current.year, current.month)
		mid_month = current.replace(day=15)
		end_of_month = current.replace(day=last_day)
		yield current, min(mid_month, end_date)
		if mid_month < end_date:
			yield mid_month, min(end_of_month + timedelta(days=1), end_date)
		next_month = (current.replace(day=1) + timedelta(days=32)).replace(day=1)
		#yield current, min(next_month, end_date)
		current = next_month

def expand_md_range(start_md: str, end_md: str, start_year: int, end_year: int):
	#ranges = []
	for year in range(start_year, end_year + 1):
		try:
			start = datetime.strptime(f"{year}-{start_md}", "%Y-%m-%d").date()
			end = datetime.strptime(f"{year}-{end_md}", "%Y-%m-%d").date()
			yield ((start, end))
		except ValueError as e:
			st.write(f"Skipping invalid date in year {year}: {e}")
	#yield ranges


st.title("iNat Bar Charts")
st.write("An app that will provide bar charts for the taxa and location of your choosing, like eBird does for birds")
st.write("(Built with the iNaturalist API, which can be a little slow)")
	

dfs = []

yes = st.text_input("Enter a taxon: ")

Numberofr = st.text_input("How many results I want: ", "10")
Numberofr = int(Numberofr)

torg = 1

Ranks = ["species", "genus", "tribe", "subfamily", "family", "superfamily", "suborder", "order", "superorder", "class"]

query = st.text_input("Enter a place (the format for a state is [State, Country code] and for a county is [County, Country code, State code]): ", placeholder="Examples: Colorado, US; Montgomery, US, MD")

rank = st.selectbox("What rank I am looking for: ", options = Ranks)
#rank="species"

if not yes:
	st.stop()

if not query:
	st.stop()
		
if not Numberofr:
	st.stop()

if not rank:
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
st.write(f"Selected taxon: {our_name}")

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
st.write(f"Selected place: {placename}")
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


firsttry = requests.get(f'https://api.inaturalist.org/v2/observations/species_counts?place_id={our_place}&rank={rank}&taxon_id={our_id}&page=1&order=desc&fields=preferred_common_name')
totalresults = firsttry.json()['results']

if totalresults == 0:
	st.write("No such thing")
	st.stop()

#time.sleep(5)
taxaids = []

CALC = """
Starting...
"""


def stream_data_ca():
    for word in list(CALC):
        yield word + " "
        time.sleep(0.1)

st.write_stream(stream_data_ca())

for x in range(0,Numberofr):
    try:
        taxaids.append(totalresults[x]['taxon']['id'])
    except:
        pass

#time.sleep(15)

observation_df_large = pl.DataFrame()

for taxonid in taxaids:
	time.sleep(1)
	response = requests.get(f'https://api.inaturalist.org/v2/observations/histogram?place_id={our_place}&taxon_id={taxonid}&order=desc&fields=species_guess%2Cobserved_on&date_field=observed&interval=week_of_year')
	observations = response.json()['results']['week_of_year']
	observation_df = pl.DataFrame(observations, strict=False, infer_schema_length=None)
	idcol = pl.Series("id", [taxonid])
	observation_df.insert_column(0, idcol)
	observation_df_large = pl.concat([observation_df_large, observation_df])


combined_df = observation_df_large
ids = combined_df.select(["id"])


successes = 0
combined_df = combined_df.with_columns(pl.col("id").cast(pl.String))
combined_df = combined_df.with_columns(rowsum = pl.sum_horizontal(cs.numeric()))
combined_df = combined_df.sort('rowsum', descending=True)
combined_df = combined_df.drop('rowsum')
ids = combined_df.select(["id"])

esttime = min(Numberofr, ids.height)

st.write(f"Translating iNat IDs to {rank} names (estimated time {esttime} seconds)...")

names = []

url = "https://api.inaturalist.org/v1/taxa/autocomplete"
for x in range(0,ids.height):
	combined_df = combined_df.group_by("id", maintain_order=True).agg(cs.numeric().sum())
	yes = ids[x,0]
	time.sleep(0.75)
	res = requests.get(f"https://api.inaturalist.org/v2/taxa?taxon_id={yes}&fields=preferred_common_name%2Cname%2Crank%2Cancestry", headers=header)
	if res.status_code != 200:
		st.write(f"Error: {res.status_code}")

	try:
		results = res.json().get("results", [])
	except:
		combined_df = combined_df.remove(pl.col("id") == str(yes))
		next

	taxon = results[0]

	ourrank = taxon['rank']

	
	#taxa = "nothing"
	
	if ourrank != rank:
		combined_df = combined_df.remove(pl.col("id") == str(yes))
		
	if rank == "species":
		try:
			taxa = (taxon['preferred_common_name'])
			names.append(taxa)
		except:
			taxa = (taxon['name'])
			names.append(taxa)
	else:
		taxa = (taxon['name'])
		names.append(taxa)
			
	combined_df = combined_df.with_columns(id = pl.when(pl.col("id") == yes).then(pl.lit(taxa)).otherwise(pl.col("id")))


combined_df = combined_df.group_by("id", maintain_order=True).agg(cs.numeric().sum())
df = combined_df.head(int(Numberofr))



#st.write(sns.load_dataset(df))

df_max = df.drop("id")
provmax = df_max.select(pl.max_horizontal("*")).max().item()
if provmax is None:
	st.write(f"No instances of {our_name} found in {placename}!")
	st.stop()
if provmax > 35:
	absolute_max = round(provmax/2)
else:
	absolute_max = round(provmax)

df_pd = df.to_pandas()
df_pd = df_pd.set_index("id")
df_pd = df_pd.dropna(how="all")  # drop rows that are all NaNs

fig, ax = plt.subplots(figsize=(16, 12))
sns.heatmap(df_pd, cmap="Purples", linewidths=0.2, linecolor='gray', vmax=absolute_max, ax=ax)

ax.set_title(f"Frequency of {our_name} in {placename}")
ax.set_xlabel("Half-Month")
ax.set_ylabel("Species")

positions = [0,4,8,12,17,21,25,30,34,38,43,47]

reallabels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

	
ylabs = df_pd.index.tolist()
ypos = range(0,len(ylabs))

ax.set_xticks(positions, rotation=45, ha="right", labels=reallabels)
st.pyplot(fig)

axes = df_pd.T.plot.line(subplots=True, sharex=True, sharey=True, ylim=(0, absolute_max), legend=False, figsize=(16,12))
fig2 = axes.flatten()[0].get_figure()
for ax, title in zip(axes.flatten(), names):
  ax.set_title(title)
plt.tight_layout()
st.pyplot(fig2)
