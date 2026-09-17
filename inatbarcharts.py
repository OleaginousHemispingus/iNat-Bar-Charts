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

Numberofy = st.text_input("How many years of data I want included (each year adds ~30 seconds): ", "2")
Numberofy = int(Numberofy)

Numberofr = st.text_input("How many results I want: ", "10")
Numberofr = int(Numberofr)

torg = 1

#Ranks = ["species", "genus", "tribe", "subfamily", "family", "superfamily", "suborder", "order", "superorder", "class"]

query = st.text_input("Enter a place (the format for a state is [State, Country code] and for a county is [County, Country code, State code]): ", placeholder="Examples: Colorado, US; Montgomery, US, MD")

#rank = st.selectbox("What rank I am looking for: ", options = Ranks)
rank="species"

if not yes:
	st.stop()

if not query:
	st.stop()
		
if not Numberofr:
	st.stop()

if not Numberofy:
	st.stop()

if not rank:
	st.stop()

res = requests.get(f"https://api.inaturalist.org/v2/taxa/autocomplete?q={yes}&fields=name%2Cpreferred_common_name%2Crank", headers=header)
if res.status_code != 200:
	st.write(f"Error: {res.status_code}")
results = res.json().get("results", [])
taxon = results[0]
try:
	our_name = taxon['preferred_common_name']
except:
	our_name = taxon['name']
st.write(f"Selected taxon: {our_name}")

res_place = requests.get(f"https://api.inaturalist.org/v2/places?q={query}&order_by=area&fields=display_name", headers=header)
if res_place.status_code != 200:
	st.write(f"Error: {res.status_code}")
results_place = res_place.json().get("results", [])
place = results_place[0]
placename = place['display_name']
st.write(f"Selected place: {placename}")
our_id = taxon['id']
our_place = place['id']

today = date.today()
firstdate = date.today() - relativedelta(years=Numberofy)
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


firsttry = requests.get(f'https://api.inaturalist.org/v2/observations?place_id={our_place}&taxon_id={our_id}&d1={firstdate}&d2={today}&page=1&order=desc')
totalresults = firsttry.json()['total_results']

if totalresults == 0:
	st.write("No such thing")
	st.stop()



#f = daterange(datetime.strptime("2024-01-01", "%Y-%m-%d"), datetime.strptime("2025-01-01", "%Y-%m-%d"))
#st.write(type(f))
#for value in f:
#	st.write(value)
	
#g = expand_md_range('01-01', '01-15', 2015, 2024)
#st.write(type(g))
#for value in g:
#	st.write(value)
startTime = datetime.now()

def find_species(taxon: int, place: int, start_md: str, end_md: str, start_year: int, end_year: int):
	#time.sleep(1.5)
	observation_df_large = pl.DataFrame(schema={"id":int, "count":int})
	
	#st.write(observation_df_large)
	for start, end in expand_md_range(start_md, end_md, start_year, end_year):
		time.sleep(1)
		#final_counts = pl.DataFrame(schema={"species_guess":str})
		observation_df_page = pl.DataFrame()
		page = 1
		max_pages = 50
		
		while page <= max_pages:
			params = {
    			'taxon_id': taxon,
   				'place_id': place,
    			'd1': start.isoformat(),
    			'd2': end.isoformat(),
    			'page': page,
    			'per_page': 200
			}
		
			#st.write(page)
			
			
			
			response = requests.get(f'https://api.inaturalist.org/v2/observations/species_counts?captive=false&place_id={place}&rank={rank}&taxon_id={taxon}&d1={start.isoformat()}&d2={end.isoformat()}&quality_grade=needs_id,research&page={page}&order=desc', headers=header)
			if response.status_code != 200:
				st.write(f"Error: {response.status_code}")
			
			#st.write(response)
			obs = response.json()
			#st.write(obs)
			observations = response.json()['results']
			#st.write(observations)
			time.sleep(1)
			
			
		
			#st.write("Gotten!!")
		#st.write(observations)
			try:
				observation_df = pl.DataFrame(observations, strict=False, infer_schema_length=None)
				#st.write(observation_df)
				#observation_df.write_csv("yes.csv")
				#observation_df = observation_df.filter(pl.col("taxon").struct.field("rank") == "species")
				#st.write(len(observation_df))
				#observation_df = observation_df.select(["species_guess"])
				#observation_df = observation_df.select(["taxon"])
				#observation_df = observation_df.select(pl.col("taxon").struct.field("id"))
				#st.write(observation_df)
				#st.write(taxon_id)
				#st.write(observation_df.columns)
				#observation_df_2 = observation_df.select(["taxon"])
				#smoop = observation_df_2[1,1]
				#smoop2 = smoop.unnest
				#st.write(observation_df_2)
				#st.write(smoop)
				observation_df_2 = observation_df.select(pl.col("taxon").struct.field("id"))
				newdf = pl.concat([observation_df_2, observation_df], how="horizontal")
				observation_df = newdf.select(pl.col("id"), pl.col("count"))
			
				
				observation_df_page = pl.concat([observation_df_page, observation_df])
				#st.write(observation_df_page)
				
				
				
				
				

				#observation_specval = observation_df_large['species_guess'].value_counts()
				#observation_specval = observation_specval.sort('count', descending=True)
				#st.write(observation_specval)
		
				#st.write(len(observation_df))
				
			except:
				break
		
			if len(observations) < 200:
				break
			
			page += 1
		
		#st.write("done")
		try:
			#st.write(observation_df_large)
			observation_df_large = pl.concat([observation_df_large, observation_df_page]).group_by("id").agg(pl.col("count").sum())
			#st.write(observation_df_large)	
		except:
			next
	
	
	#observation_specval = observation_df_large['id'].value_counts()
	observation_specval = observation_df_large.sort('count', descending=True)
	
			#st.write(observation_specval)
			#sum_row_data = {"species_guess": "Total", "count": int(observation_specval["count"].sum())}
			#sum_df = pl.DataFrame([sum_row_data])
			#specval = pl.concat([observation_specval, sum_df])
	#specval = observation_specval.with_columns(((pl.col("count") / int(observation_specval["count"].sum()) * 100).round(2).alias(f"p_{start}")))
	specval = observation_specval.with_columns(((pl.col("count") / int(observation_specval["count"].sum()) * 100).round(2).alias(f"p_{start}")))
	specval2 = observation_specval.with_columns(((pl.col("count").alias(f"p_{start}"))))
	specval2 = specval2.select(["id", f"p_{start}"])
	specval = specval.select(["id", f"p_{start}"])
	
	#st.write(specval)
	#dfs.append(specval)
			#percentage = specval.select(pl.col(f"p_{start}"))
			#if torg == 1:
				#st.write("torg!")
				#final_counts = specval
			#else:
				#final_counts = final_counts.join(specval, on="species_guess", how="full", coalesce=True)
				#final_counts = final_counts.with_columns(pl.coalesce([pl.col("species_guess"), pl.col("species_guess_right")]).alias("species_guess")).drop("species_guess_right")
		#torg = 2
	
	return specval2

def find_observations(taxon: int, place: int, start: str, end: str):
	big_specval = []
	#time.sleep(1.5)
	observation_df_large = pl.DataFrame()

	page = 1
	max_pages = 60
	while page <= max_pages:
		response = requests.get(f'https://api.inaturalist.org/v2/observations?place_id={place}&taxon_id={taxon}&d1={start}&d2={end}&per_page=200&page={page}&order=desc&order_by=observed_on&fields=species_guess%2Cobserved_on%2Ctaxon')
		observations = response.json()['results']
	

		try:
			observation_df = pl.DataFrame(observations, strict=False, infer_schema_length=None)
			observation_df_large = pl.concat([observation_df_large, observation_df])
				
		except:
			break
		
		
		if len(observations) < 200:
			break
			
		
		page += 1
		time.sleep(1)
		
		#print("done")
	for row in range(observation_df_large.height):
		newvalue = (observation_df_large.item(row, "observed_on")[5:])
		observation_df_large[row, "observed_on"] = newvalue

	observation_df_large = observation_df_large.sort('observed_on', descending=False)

	df_grouped = observation_df_large.with_columns(
    	group_id=pl.sum_horizontal(
        	[(pl.col("observed_on") >= d).cast(pl.Int32) for d in date_starts]
    	)
	)

	df_list = df_grouped.partition_by("group_id", include_key=True)

	for x in range(1, len(date_starts)):
		ourdf = df_list[x-1]
		thisdate = ourdf.item(0,"group_id")
		if thisdate!= x:
			newdf = pl.DataFrame(schema={"id":int, f"p_{date_starts[x-1]}":float})
			df_list.insert(x-1, newdf)

	if df_list[-1].item(0,"group_id") != 24:
		newdf = pl.DataFrame(schema={"id":int, f"p_{date_starts[-1]}":float})
		df_list.append(newdf)


	numm = 0

	for observation_df_halfmonth in df_list:
		try:
			observation_df_halfmonth = observation_df_halfmonth.select(pl.col("taxon").struct.field("id"))
			observation_specval = observation_df_halfmonth['id'].value_counts()
			observation_specval = observation_specval.sort('count', descending=True)
			specval = observation_specval.with_columns(((pl.col("count") / int(observation_specval["count"].sum()) * 100).round(2).alias(f"p_{date_starts[numm]}")))
			specval2 = observation_specval.with_columns(((pl.col("count").alias(f"p_{date_starts[numm]}"))))
			specval2 = specval2.select(["id", f"p_{date_starts[numm]}"])
			specval = specval.select(["id", f"p_{date_starts[numm]}"])
			big_specval.append(specval2)
		except:
			(big_specval.append(observation_df_halfmonth))
		numm += 1
	#observation_specval = observation_df_large.sort('count', descending=True)
	
			#print(observation_specval)
			#sum_row_data = {"species_guess": "Total", "count": int(observation_specval["count"].sum())}
			#sum_df = pl.DataFrame([sum_row_data])
			#specval = pl.concat([observation_specval, sum_df])
	#specval = observation_specval.with_columns(((pl.col("count") / int(observation_specval["count"].sum()) * 100).round(2).alias(f"p_{start}")))
	#specval = observation_specval.with_columns(((pl.col("count") / int(observation_specval["count"].sum()) * 100).round(2).alias(f"p_{start}")))
	#specval2 = observation_specval.with_columns(((pl.col("count").alias(f"p_{start}"))))
	#specval2 = specval2.select(["id", f"p_{start}"])
	#specval = specval.select(["id", f"p_{start}"])
	
	#print(specval)
	#dfs.append(specval)
			#percentage = specval.select(pl.col(f"p_{start}"))
			#if torg == 1:
				#print("torg!")
				#final_counts = specval
			#else:
				#final_counts = final_counts.join(specval, on="species_guess", how="full", coalesce=True)
				#final_counts = final_counts.with_columns(pl.coalesce([pl.col("species_guess"), pl.col("species_guess_right")]).alias("species_guess")).drop("species_guess_right")
		#torg = 2
	
	return big_specval
	
	
date_ranges = [
    ('01-01', '01-15'),
    ('01-16', '01-31'),
    ('02-01', '02-15'),
    ('02-16', '02-28'),
    ('03-01', '03-15'),
    ('03-16', '03-31'),
    ('04-01', '04-15'),
    ('04-16', '04-30'),
    ('05-01', '05-15'),
    ('05-16', '05-31'),
    ('06-01', '06-15'),
    ('06-16', '06-30'),
    ('07-01', '07-15'),
    ('07-16', '07-31'),
    ('08-01', '08-15'),
    ('08-16', '08-31'),
    ('09-01', '09-15'),
    ('09-16', '09-30'),
    ('10-01', '10-15'),
    ('10-16', '10-31'),
    ('11-01', '11-15'),
    ('11-16', '11-30'),
    ('12-01', '12-15'),
    ('12-16', '12-31')
]		
			
results = []


CALC = """
Starting...
"""


def stream_data_ca():
    for word in list(CALC):
        yield word + " "
        time.sleep(0.1)
    
        
st.write_stream(stream_data_ca())


date_ranges_1 = date_ranges[0:(dateindex)]
date_ranges_2 = date_ranges[dateindex:]

with ThreadPoolExecutor(max_workers=2) as executor:
	if totalresults > 10000 or rank != "species":
		if Numberofy*30 < 60:
			st.write(f"Estimated time: {Numberofy*30} seconds")
		else:
			st.write(f"Estimated time: {Numberofy/2} minutes")
		futures = {
			executor.submit(
                find_species,
                our_id,
                our_place,
                start_date,
                end_date,
                firstdate.year + 1,
                today.year
			): (start_date, end_date)
			for start_date, end_date in date_ranges_1
		}

		for future in as_completed(futures):
			start_date, end_date = futures[future]
		
			try:
				result = future.result()
				results.append({
					"start_date": start_date,
					"end_date": end_date,
					"data": result
				})
				st.write(f"Finished {start_date} to {end_date}")
		
			except Exception as e:
				st.write(f"Error for {start_date} to {end_date}: {e}")
					
		futures = {
			executor.submit(
				find_species,
				our_id,
				our_place,
				start_date,
				end_date,
				firstdate.year,
				today.year - 1
			): (start_date, end_date)
			for start_date, end_date in date_ranges_2
		}
		
		for future in as_completed(futures):
			start_date, end_date = futures[future]
	
			try:
				result = future.result()
				results.append({
					"start_date": start_date,
					"end_date": end_date,
					"data": result
				})
				st.write(f"Finished {start_date} to {end_date}")
	
			except Exception as e:
				st.write(f"Error for {start_date} to {end_date}: {e}")

		results.sort(key=lambda x: date_ranges.index(
    		(x["start_date"], x["end_date"])
		))

		for result in results:
			dfs.append(result['data'])
		combined_df = reduce(lambda left, right: left.join(right, on="id", how="full", coalesce=True), dfs)
		combined_df = combined_df.fill_null(0)
        

	else: 
		st.write(f"Estimated time: {math.ceil(totalresults/200)*4} seconds")
		result = find_observations(our_id, our_place, str(firstdate), str(today))
		combined_df = reduce(lambda left, right: left.join(right, on="id", how="full", coalesce=True), result)
		combined_df = combined_df.fill_null(0)


successes = 0
combined_df = combined_df.with_columns(pl.col("id").cast(pl.String))
combined_df = combined_df.with_columns(rowsum = pl.sum_horizontal(cs.numeric()))
combined_df = combined_df.sort('rowsum', descending=True)
combined_df = combined_df.drop('rowsum')
ids = combined_df.select(["id"])

esttime = min(Numberofr, ids.height)

st.write(f"Translating iNat IDs to {rank} names (estimated time {esttime} seconds)...")

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
	#	if rank == 'genus':
	#		taxa = taxon['name'].split(" ")[0]
	#		break
	#	if len(taxon['ancestry'].split("/")[-1]) == 1:
	#		combined_df = combined_df.remove(pl.col("id") == str(yes))
	#		break

	#	ancestor = taxon['ancestry'].split("/")[-1]
	#	time.sleep(1)
	#	tryagain = requests.get(f"https://api.inaturalist.org/v2/taxa?taxon_id={ancestor}&fields=preferred_common_name%2Cname%2Crank%2Cancestry", headers=header)
	#	results = tryagain.json().get("results", [])
	#	tryagaintaxon = results[0]
	#	if ourrank == "complex" and rank == "species":
	#		ourrank = "species"
	#	else:
	#		ourrank = tryagaintaxon['rank']
	#		taxon = tryagaintaxon
		#combined_df = combined_df.remove(pl.col("id") == str(yes))
		
	if rank == "species":
		try:
			taxa = (taxon['preferred_common_name'])
		except:
			taxa = (taxon['name'])
	else:
		taxa = (taxon['name'])
			
	combined_df = combined_df.with_columns(id = pl.when(pl.col("id") == yes).then(pl.lit(taxa)).otherwise(pl.col("id")))
	successes += 1
	#if taxon['rank'] != 'species':
	#	combined_df = combined_df.remove(pl.col("id") == str(yes))
	#else:
	#	combined_df = combined_df.with_columns(id = pl.when(pl.col("id") == yes).then(pl.lit(species)).otherwise(pl.col("id")))
	#	successes += 1
	if successes == int(Numberofr):
		combined_df = combined_df.head(int(Numberofr))
		break


combined_df = combined_df.group_by("id", maintain_order=True).agg(cs.numeric().sum())
df = combined_df.head(int(Numberofr))



#st.write(sns.load_dataset(df))

df_max = df.drop("id")
provmax = df_max.select(pl.max_horizontal("*")).max().item()
if provmax == 0:
	st.write("No instances of {our_name} found in {placename}!")
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

positions = range(0, len(df_pd.columns), 2)
labels = df_pd.columns[::2]

reallabels = []

if totalresults > 10000:
	for label in labels:
		reallabels.append(label[7:])

else:
	for label in labels:
		reallabels.append(label[2:])
	
ylabs = df_pd.index.tolist()
ypos = range(0,len(ylabs))

ax.set_xticks(positions, rotation=45, ha="right", labels=reallabels)
st.pyplot(fig)
