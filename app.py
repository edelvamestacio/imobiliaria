import streamlit as st
from controller.MainController import MainController

if __name__ == '__main__':

    st.set_page_config(layout="wide", page_title="Dashboard Imobiliário")

    app = MainController()
    app.run()