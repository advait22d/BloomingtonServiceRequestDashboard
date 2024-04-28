

import streamlit as st
import pandas as pd
from pymongo import MongoClient
import pydeck as pdk
import datetime
import plotly.express as px


# client = MongoClient("mongodb+srv://adt:adtroot@spendem.bjwbooc.mongodb.net/")
# client = MongoClient("mongodb+srv://adt:adtroo@spendem.bjwbooc.mongodb.net/?retryWrites=true&w=majority&appName=spendem")
client = MongoClient(st.secrets["mongo"]["uri"])


db = client.bloomington_service_request
collection = db.service_request_2024

def main():
    st.title("Bloomington Service Request Management")

    
    with st.form("service_request_form"):
        st.subheader("Add Service Request")
        service_request_id = st.number_input("Service Request ID", format="%d", min_value=1)
        requested_datetime = st.date_input("Requested Datetime")
        updated_datetime = st.date_input("Updated Datetime")
        closed_date = st.date_input("Closed Date")
        requested_time = st.text_input("Requested Time (HH:MM[:SS])", "00:00:00")
        updated_time = st.text_input("Updated Time (HH:MM[:SS])", "00:00:00")
        closed_time = st.text_input("Closed Time (HH:MM[:SS])", "00:00:00")
        status_description = st.text_input("Status Description")
        source = st.text_input("Source")
        service_name = st.text_input("Service Name")
        description = st.text_area("Description")
        agency_responsible = st.text_input("Agency Responsible")
        address =  st.text_input("Address") 
        lat = st.number_input(label='Latitude', format="%.2f")
        long = st.number_input(label='longitude',format="%.2f")
        zipcode = st.number_input("Zipcode")
        submit_button = st.form_submit_button("Submit Request")

    
    if submit_button:
        process_submission(service_request_id, requested_datetime, updated_datetime, closed_date, requested_time, updated_time, closed_time,
                           status_description, source, service_name, description, agency_responsible, address, lat, long, zipcode)


    
    with st.form("update_service_request_form"):
        st.subheader("Update Service Request")
        update_service_request_id = st.number_input("Enter Service Request ID to Update", format="%d", min_value=1)
        new_requested_datetime = st.date_input("New Requested Datetime")
        new_updated_datetime = st.date_input("New Updated Datetime")
        new_closed_date = st.date_input("New Closed Date")
        new_requested_time = st.text_input("New Requested Time (HH:MM[:SS])", "00:00:00")
        new_updated_time = st.text_input("New Updated Time (HH:MM[:SS])", "00:00:00")
        new_closed_time = st.text_input("New Closed Time (HH:MM[:SS])", "00:00:00")
        new_status_description = st.text_input("New Status Description")
        new_source = st.text_input("New Source")
        new_service_name = st.text_input("New Service Name")
        new_description = st.text_area("New Description")
        new_agency_responsible = st.text_input("New Agency Responsible")
        new_address =  st.text_input("New Address")
        new_lat = st.number_input("New Latitude", format="%.2f")
        new_long = st.number_input("New Longitude", format="%.2f")
        new_zipcode = st.number_input("New Zipcode")
        update_button = st.form_submit_button("Update Request")

    
    if update_button:
        process_update(update_service_request_id, new_requested_datetime, new_updated_datetime, new_closed_date,
                    new_requested_time, new_updated_time, new_closed_time, new_status_description, new_source, 
                    new_service_name, new_description, new_agency_responsible, new_address, new_lat, new_long, new_zipcode)


   
    with st.form("delete_service_request_form"):
        st.subheader("Delete Service Request")
        delete_service_request_id = st.number_input("Enter Service Request ID to Delete", format="%d", min_value=1)
        delete_button = st.form_submit_button("Delete Request")

    
    if delete_button:
        process_deletion(delete_service_request_id)

    
    st.subheader("Geospatial Data Visualization of Service Requests")
    start_date = st.date_input("Start Date", value=datetime.datetime.now() - datetime.timedelta(days=45))
    end_date = st.date_input("End Date", value=datetime.datetime.now())
    map_section(start_date, end_date)
    #Stats
    service_names = fetch_unique_service_names()
    selected_services = st.multiselect("Select Service Names", service_names)
    generate_statistics_and_graphs(start_date, end_date,selected_services)


def process_submission(service_request_id, requested_datetime, updated_datetime, closed_date, requested_time, updated_time, closed_time,
                       status_description, source, service_name, description, agency_responsible, address, lat, long, zipcode):
    try:
        
        requested_datetime = datetime.datetime.combine(requested_datetime, datetime.datetime.strptime(requested_time, "%H:%M:%S").time())
        updated_datetime = datetime.datetime.combine(updated_datetime, datetime.datetime.strptime(updated_time, "%H:%M:%S").time())
        closed_date = datetime.datetime.combine(closed_date, datetime.datetime.strptime(closed_time, "%H:%M:%S").time())

        service_request_data = {
            "service_request_id": service_request_id,
            "requested_datetime": requested_datetime,
            "updated_datetime": updated_datetime,
            "closed_date": closed_date,
            "status_description": status_description,
            "source": source,
            "service_name": service_name,
            "description": description,
            "agency_responsible": agency_responsible,
            "address": address,
            "lat": lat,
            "long": long,
            "zipcode": zipcode
        }

        collection.insert_one(service_request_data)
        st.success("Service request added successfully!")
    except Exception as e:
        st.error(f"Failed to insert service request: {e}")

def process_deletion(service_request_id):
    try:
        result = collection.delete_one({"service_request_id": service_request_id})
        if result.deleted_count > 0:
            st.success(f"Service request ID {service_request_id} deleted successfully!")
        else:
            st.error(f"No service request found with ID {service_request_id}")
    except Exception as e:
        st.error(f"Failed to delete service request: {e}")

def map_section(start_date, end_date):
    
    

    try:
        
        start_datetime = datetime.datetime.combine(start_date, datetime.time.min)
        end_datetime = datetime.datetime.combine(end_date, datetime.time.max)

        
        query = {
            "requested_datetime": {"$gte": start_datetime, "$lte": end_datetime},
            "lat": {"$exists": True},
            "long": {"$exists": True}
        }
        projection = {'lat': 1, 'long': 1, '_id': 0}
        documents = list(collection.find(query, projection))

        if documents:
            
            df = pd.DataFrame(documents)

            
            df['lat'] = df['lat'].astype(float)
            df['long'] = df['long'].astype(float)

            
            layer = pdk.Layer(
                "ScatterplotLayer",
                data=df,
                get_position='[long, lat]',
                get_color='[200, 30, 0, 160]',
                get_radius=50,
                pickable=True
            )

            
            view_state = pdk.ViewState(latitude=df['lat'].mean(), longitude=df['long'].mean(), zoom=11)

            
            r = pdk.Deck(layers=[layer], initial_view_state=view_state, map_style="mapbox://styles/mapbox/streets-v12")
            st.pydeck_chart(r)
        else:
            st.write("No geospatial data available.")
    except Exception as e:
        st.error(f"Failed to fetch or plot data: {e}")


def fetch_unique_service_names():
    return collection.distinct("service_name")
def generate_statistics_and_graphs(start_date, end_date, selected_services):
    try:
        start_datetime = datetime.datetime.combine(start_date, datetime.time.min)
        end_datetime = datetime.datetime.combine(end_date, datetime.time.max)

       
        query = {
            "requested_datetime": {"$gte": start_datetime, "$lte": end_datetime}
        }
        projection = {'requested_datetime': 1, 'service_name': 1, '_id': 0}
        documents = list(collection.find(query, projection))

        if documents:
            df = pd.DataFrame(documents)
            df['requested_datetime'] = pd.to_datetime(df['requested_datetime'])
            df['date'] = df['requested_datetime'].dt.date
            df['date_str'] = df['date'].astype(str)

            if not selected_services:
                selected_services = df['service_name'].unique().tolist() 

            daily_counts = df['date_str'].value_counts().sort_index()
            st.subheader("Daily Requests Bar Chart")
            st.bar_chart(daily_counts)

            
            filtered_df = df[df['service_name'].isin(selected_services)]

            
            daily_grouped = filtered_df.groupby(['date_str', 'service_name']).size().reset_index(name='counts')

            
            fig = px.line(daily_grouped, x='date_str', y='counts', color='service_name', 
                          title='Daily Requests by Service', labels={'date_str': 'Date', 'counts': 'Number of Requests'})
            st.plotly_chart(fig)

           
            st.subheader("Summary Statistics for All Selected Services")
            st.text(f"Total Requests: {len(df)}")
            st.text(f"Average Daily Requests: {daily_grouped['counts'].mean():.2f}")
            st.text(f"Maximum Requests in a Day: {daily_grouped['counts'].max()}")
            st.text(f"Minimum Requests in a Day: {daily_grouped['counts'].min()}") 
        else:
            st.write("No data available for the selected dates.")
    except Exception as e:
        st.error(f"Failed to fetch data or plot graphs: {e}")


def process_update(service_request_id, requested_datetime, updated_datetime, closed_date,
                   requested_time, updated_time, closed_time, status_description, source, 
                   service_name, description, agency_responsible, address, lat, long, zipcode):
    try:
        
        service_request = collection.find_one({"service_request_id": service_request_id})
        if service_request:
            
            requested_datetime = datetime.datetime.combine(requested_datetime, datetime.datetime.strptime(requested_time, "%H:%M:%S").time())
            updated_datetime = datetime.datetime.combine(updated_datetime, datetime.datetime.strptime(updated_time, "%H:%M:%S").time())
            closed_date = datetime.datetime.combine(closed_date, datetime.datetime.strptime(closed_time, "%H:%M:%S").time())

            
            new_values = {"$set": {
                "requested_datetime": requested_datetime,
                "updated_datetime": updated_datetime,
                "closed_date": closed_date,
                "status_description": status_description,
                "source": source,
                "service_name": service_name,
                "description": description,
                "agency_responsible": agency_responsible,
                "address": address,
                "lat": lat,
                "long": long,
                "zipcode": zipcode
            }}
            collection.update_one({"service_request_id": service_request_id}, new_values)
            st.success(f"Service request ID {service_request_id} updated successfully!")
        else:
            st.error(f"No service request found with ID {service_request_id}")
    except Exception as e:
        st.error(f"Failed to update service request: {e}")


if __name__ == "__main__":
    main()
