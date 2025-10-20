import pandas as pd
import streamlit as st
import plotly.express as px
import json
import os


class DashboardVentes:
    def __init__(self):
        self.df_douala = None
        self.df_yaounde = None
        self.df_garoua = None
        self.df_global = None

    def charger_donnees_douala(self, fichier_excel):
        """Charger les données Excel de Douala"""
        self.df_douala = pd.read_excel(fichier_excel)
        self.df_douala['Agence'] = 'Douala'
        return self.df_douala

    def charger_donnees_yaounde(self, fichier_csv):
        """Charger les données CSV de Yaoundé"""
        self.df_yaounde = pd.read_csv(fichier_csv)
        self.df_yaounde['Agence'] = 'Yaoundé'
        return self.df_yaounde

    def charger_donnees_garoua(self, fichier_json):
        """Charger les données JSON de Garoua"""
        with open(fichier_json, 'r') as f:
            data = json.load(f)
        self.df_garoua = pd.DataFrame(data)
        self.df_garoua['Agence'] = 'Garoua'
        return self.df_garoua

    def consolidere_donnees(self):
        """Consolider toutes les données"""
        frames = [self.df_douala, self.df_yaounde, self.df_garoua]
        self.df_global = pd.concat(frames, ignore_index=True)

        # Standardiser les dates si nécessaire
        if 'Date' in self.df_global.columns:
            self.df_global['Date'] = pd.to_datetime(self.df_global['Date'])
            self.df_global['Mois'] = self.df_global['Date'].dt.month
            self.df_global['Mois_Nom'] = self.df_global['Date'].dt.strftime('%B')

        return self.df_global

    def calculer_kpis(self):
        """Calculer tous les KPI"""
        if self.df_global is None:
            return {}

        total_global = self.df_global['Montant'].sum()

        # Par agence
        ventes_par_agence = self.df_global.groupby('Agence')['Montant'].sum()

        # Par vendeur
        ventes_par_vendeur = self.df_global.groupby(['Agence', 'Vendeur'])['Montant'].sum()

        # Par mois
        ventes_par_mois = self.df_global.groupby(['Mois', 'Mois_Nom'])['Montant'].sum()

        return {
            'total_global': total_global,
            'par_agence': ventes_par_agence,
            'par_vendeur': ventes_par_vendeur,
            'par_mois': ventes_par_mois
        }


def main():
    st.set_page_config(page_title="Dashboard Ventes", layout="wide")
    st.title("📊 Tableau de Bord des Ventes - Agences Cameroun")

    # Initialisation
    dashboard = DashboardVentes()

    # Sidebar pour upload des fichiers
    st.sidebar.header("📁 Import des Données")

    fichier_douala = st.sidebar.file_uploader("Agence Douala (Excel)", type=['xlsx'])
    fichier_yaounde = st.sidebar.file_uploader("Agence Yaoundé (CSV)", type=['csv'])
    fichier_garoua = st.sidebar.file_uploader("Agence Garoua (JSON)", type=['json'])

    if fichier_douala and fichier_yaounde and fichier_garoua:
        try:
            # Chargement des données
            dashboard.charger_donnees_douala(fichier_douala)
            dashboard.charger_donnees_yaounde(fichier_yaounde)
            dashboard.charger_donnees_garoua(fichier_garoua)

            # Consolidation
            df_global = dashboard.consolidere_donnees()
            kpis = dashboard.calculer_kpis()

            # Affichage des KPI principaux
            st.header("📈 KPI Globaux")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Ventes Globales", f"{kpis['total_global']:,.0f} FCFA")

            with col2:
                st.metric("Nombre de Ventes", len(df_global))

            with col3:
                st.metric("Nombre de Vendeurs", df_global['Vendeur'].nunique())

            with col4:
                st.metric("Période Couverte",
                          f"{df_global['Date'].min().strftime('%d/%m/%Y')} - {df_global['Date'].max().strftime('%d/%m/%Y')}")

            # Visualisations
            st.header("📊 Analyses Détailées")

            col1, col2 = st.columns(2)

            with col1:
                # Ventes par agence
                fig_agence = px.pie(
                    values=kpis['par_agence'].values,
                    names=kpis['par_agence'].index,
                    title="Répartition des Ventes par Agence"
                )
                st.plotly_chart(fig_agence)

            with col2:
                # Ventes par mois
                fig_mois = px.bar(
                    x=kpis['par_mois'].index.get_level_values('Mois_Nom'),
                    y=kpis['par_mois'].values,
                    title="Ventes par Mois"
                )
                st.plotly_chart(fig_mois)

            # Tableau détaillé par vendeur
            st.subheader("🏆 Performance par Vendeur")
            df_vendeurs = kpis['par_vendeur'].reset_index()
            st.dataframe(df_vendeurs.sort_values('Montant', ascending=False))

            # Données brutes
            st.subheader("📋 Données Consolidées")
            st.dataframe(df_global)

        except Exception as e:
            st.error(f"Erreur lors du traitement: {str(e)}")

    else:
        st.info("Veuillez uploader les fichiers des 3 agences pour commencer")


if __name__ == "__main__":
    main()