# Import python packages
import streamlit as st
#from snowflake.snowpark.context import get_active_session
from snowflake.snowpark.functions import col #when_matched
import requests 

# Write directly to the app
st.title(f":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")
st.write(
  """Choose the fruit you want in your custom Smoothie!"""
)

name_on_order = st.text_input('Name on smoothie:')
st.write('The name on your smoothie will be ', name_on_order)

cnx = st.connection("snowflake")
session = cnx.session()
my_dataframe = session.table("smoothies.public.fruit_options").select(col('fruit_name'),col('search_on'))
st.dataframe(data=my_dataframe, use_container_width=True)
st.stop()

#Convert the snowpark Dataframe to a Pandas Dataframe so we can use the LOC  function
pd_df = my_dataframe.to_pandas()
#st.dataframe(pd_df)
#st.stop()

my_dataframe = session.table("smoothies.public.orders") \
    .filter(col("ORDER_FILLED") == 0) \
    .collect()
# For the smoothie order form
fruit_dataframe = session.table("smoothies.public.fruit_options").select(col('fruit_name'))
# For the pending orders editor
pending_orders = session.table("smoothies.public.orders") \
    .filter(col("ORDER_FILLED") == 0) \
    .collect()


if my_dataframe:
    editable_df = st.data_editor(my_dataframe)
    submitted = st.button('Submit')

    if submitted:
#    st.success('Someone clicked the button.', icon='👍')    
        og_dataset = session.table("smoothies.public.orders")
        edited_dataset = session.create_dataframe(editable_df)

        try:
            og_dataset.merge(edited_dataset
                             , (og_dataset['ORDER_UID'] == edited_dataset['ORDER_UID'])
                             , [when_matched().update({'ORDER_FILLED': edited_dataset['ORDER_FILLED']})]
                            )   
            st.success("Order(s) Updated!", icon='👍')
        except:
            st.write('Something went wrong.')

else:
    st.success('There are no pending orders right now', icon='👍')

    
ingredients_list = st.multiselect(
    'Choose up to 5 ingredients: '
    , fruit_dataframe
    , max_selections = 5
)

if ingredients_list:

    ingredients_string = ''

    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '
      
        search_on=pd_df.loc[pd_df['fruit_name'] == fruit_chosen, 'search_on'].iloc[0]
        st.write('The search value for: ', fruit_chosen, ' is ', search_on,'.')
      
        st.subheader(fruit_chosen + ' Nutrition Information')
        smoothiefroot_response = requests.get("https://my.smoothiefroot.com/api/fruit/{search_on}")  
        sf_df = st.dataframe(data=smoothiefroot_response.json(), use_container_width=True)

    st.write(ingredients_string, name_on_order)
    my_insert_stmt = """ insert into smoothies.public.orders(ingredients, name_on_order)
                    values ('""" + ingredients_string + """', '""" + name_on_order + """')"""

    time_to_insert = st.button('Submit Order')
    if time_to_insert:
        session.sql(my_insert_stmt).collect()
        st.success('Your Smoothie is ordered!', icon="✅")

