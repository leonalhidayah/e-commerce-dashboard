import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from babel.numbers import format_currency
from plotly.subplots import make_subplots


# helper function
def create_daily_orders_df(df: pd.DataFrame) -> pd.DataFrame:
    daily_orders_df = (
        df.resample(rule="D", on="order_purchase_timestamp")
        .agg({"order_id": "nunique", "price": "sum"})
        .reset_index()
    )

    daily_orders_df.columns = ["order_date", "order_count", "revenue"]

    return daily_orders_df


def create_total_customer_by_city_df(df: pd.DataFrame) -> pd.DataFrame:
    total_customer_by_city_df = (
        df.groupby(by="customer_city")
        .agg(
            {
                "geolocation_lat": "mean",
                "geolocation_lng": "mean",
                "customer_unique_id": "nunique",
            }
        )
        .rename(columns={"customer_unique_id": "total_customer"})
        .reset_index()
        .sort_values(by="total_customer", ascending=False)
    )

    return total_customer_by_city_df


def create_product_category_sales_df(df: pd.DataFrame) -> pd.DataFrame:
    product_category_sales_df = (
        df.groupby(by="product_category_name_english")
        .agg(
            total_product=("product_id", "nunique"),
            total_order=("order_id", "nunique"),
            total_price=("price", "sum"),
            total_freight=("freight_value", "sum"),
        )
        .sort_values(by="total_order", ascending=False)
        .reset_index()
    )

    return product_category_sales_df


def create_rfm_df(df: pd.DataFrame) -> pd.DataFrame:
    rfm_df = df.groupby(by="customer_unique_id", as_index=False).agg(
        {
            "order_purchase_timestamp": "max",
            "order_id": "nunique",
            "price": "sum",
        }
    )

    latest_date = pd.Timestamp("2018-09-03 09:06:57")
    rfm_df["order_purchase_timestamp"] = (
        latest_date - rfm_df["order_purchase_timestamp"]
    ).dt.days
    rfm_df.rename(
        columns={
            "order_purchase_timestamp": "recency",
            "order_id": "frequency",
            "price": "monetary",
        },
        inplace=True,
    )
    rfm_df["customer_label_id"] = "C" + pd.Series(np.arange(95420).astype(str))

    return rfm_df


# import and prepare data
df = pd.read_csv(
    "dashboard/main_data.csv",
    parse_dates=[
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
        "shipping_limit_date",
    ],
)

max_date = df["order_purchase_timestamp"].max()
min_date = df["order_purchase_timestamp"].min()

st.set_page_config(layout="wide")

# sidebar
with st.sidebar:
    st.markdown("""
                # Leonhard Corp.
                """)

    start_date, end_date = st.date_input(
        label="Date Filter",
        min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date],
    )

main_df = df[
    (df["order_purchase_timestamp"].dt.date >= start_date)
    & (df["order_purchase_timestamp"].dt.date <= end_date)
]

daily_orders_df = create_daily_orders_df(main_df)
total_customer_by_city_df = create_total_customer_by_city_df(main_df)
product_category_sales_df = create_product_category_sales_df(main_df)
rfm_df = create_rfm_df(main_df)

# content
st.header("Dasboard Report Brazilian E-Commerce Data")

st.subheader("Daily Orders")

col1, col2 = st.columns(2)

## sales metric
with col1:
    total_orders = daily_orders_df["order_count"].sum()
    st.metric("Total orders", value=total_orders)

## revenue metric
with col2:
    total_revenue = format_currency(
        daily_orders_df["revenue"].sum(), "R$", locale="es_US"
    )
    st.metric("Total Revenue", value=total_revenue)

## revenue chart daily
fig = px.line(daily_orders_df, x="order_date", y="revenue", markers="o")
st.plotly_chart(fig)

## product performances
st.subheader("Best & Worst Performing Product")

col1, col2 = st.columns(2)

with col1:
    color_map = {}
    temp_df = product_category_sales_df.head(5)

    for k, v in zip(temp_df["product_category_name_english"], temp_df["total_order"]):
        if v == temp_df["total_order"].max():
            color_map[k] = "#1C325B"
        else:
            color_map[k] = "#B3C8CF"

    fig = px.bar(
        temp_df,
        y="product_category_name_english",
        x="total_order",
        text_auto=True,
        color="product_category_name_english",
        color_discrete_map=color_map,
    )

    fig.update_layout(
        showlegend=False,
        xaxis={"visible": False, "showticklabels": False},
        yaxis_title=None,
        title="<b>Top 5 Best Performing Products</b>",
    )

    st.plotly_chart(fig)

with col2:
    color_map = {}
    temp_df = product_category_sales_df.tail(5)

    for k, v in zip(temp_df["product_category_name_english"], temp_df["total_order"]):
        if v == temp_df["total_order"].min():
            color_map[k] = "#FF004D"
        else:
            color_map[k] = "#B3C8CF"

    fig = px.bar(
        temp_df,
        y="product_category_name_english",
        x="total_order",
        text_auto=True,
        color="product_category_name_english",
        color_discrete_map=color_map,
    )

    fig.update_layout(
        showlegend=False,
        xaxis={"visible": False, "showticklabels": False},
        yaxis_title=None,
        title="<b>Top 5 Worst Performing Products</b>",
    )

    st.plotly_chart(fig)

## customer geography
st.subheader("Customer Geography")
### city
color_map = {}
temp_df = total_customer_by_city_df.head(5)
for k, v in zip(temp_df["customer_city"], temp_df["total_customer"]):
    if v == temp_df["total_customer"].max():
        color_map[k] = "#1C325B"
    else:
        color_map[k] = "#B3C8CF"

fig = px.bar(
    temp_df,
    y="customer_city",
    x="total_customer",
    text_auto=True,
    color="customer_city",
    color_discrete_map=color_map,
)

fig.update_layout(
    showlegend=False,
    xaxis={"visible": False, "showticklabels": False},
    yaxis_title=None,
    title="<b>Top 5 Number of Customer by City</b>",
)

fig.update_traces(textposition="outside")

st.plotly_chart(fig)

st.map(
    total_customer_by_city_df,
    latitude="geolocation_lat",
    longitude="geolocation_lng",
)

### RFM
st.subheader("RFM Analysis")
st.dataframe(rfm_df)

fig = make_subplots(
    rows=1,
    cols=3,
    # subplot_titles=["by recency", "by frequency", "by monetary"]
)

for i, col in enumerate(["recency", "frequency", "monetary"]):
    temp_df = rfm_df.sort_values(
        by=col, ascending=[True if col == "recency" else False]
    ).head(5)
    fig.add_trace(
        go.Bar(
            x=temp_df["customer_label_id"],
            y=temp_df[col],
            text=temp_df[col],
            marker_color="#B3C8CF",
            textposition="outside",
        ),
        row=1,
        col=i + 1,
    )

fig.update_layout(
    xaxis_title_text="Customer by Recency",
    xaxis2_title_text="Customer by Frequency",
    xaxis3_title_text="Customer by Monetary",
    showlegend=False,
    yaxis1={"visible": False},
    yaxis2={"visible": False},
    yaxis3={"visible": False},
    title="<b>Top 5 Customers Based on RFM Values</b>",
)

st.plotly_chart(fig)
