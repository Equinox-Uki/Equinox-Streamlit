import streamlit as st
import pandas as pd
import plotly.express as px

# Konfigurasi Halaman
st.set_page_config(page_title="Dashboard Kinerja & Keuangan Daerah", layout="wide")

# --- SIDEBAR: Upload File ---
st.sidebar.header("1. Unggah Dataset")
st.sidebar.write("Silakan unggah file data Anda (misalnya: **dataset_fiskal_97_hipoFull.csv**)")
uploaded_file = st.sidebar.file_uploader("Pilih file CSV", type=["csv"])

# --- MAIN PAGE ---
st.title("📊 Dashboard Kinerja & Keuangan Daerah")

# Jika file sudah diunggah
if uploaded_file is not None:
    # Membaca data yang diunggah
    df = pd.read_csv(uploaded_file)
    
    st.success("File berhasil diunggah!")
    
    # --- SIDEBAR: Filter Data ---
    st.sidebar.header("2. Filter Data")
    
    # Memastikan kolom 'Kota' dan 'Tahun' ada di dataset untuk filter
    if 'Kota' in df.columns and 'Tahun' in df.columns:
        # Filter Kota
        daftar_kota = df['Kota'].unique()
        kota_pilihan = st.sidebar.multiselect(
            "Pilih Kota:",
            options=daftar_kota,
            default=daftar_kota[:3] if len(daftar_kota) >= 3 else daftar_kota
        )

        # Filter Tahun
        min_tahun = int(df['Tahun'].min())
        max_tahun = int(df['Tahun'].max())
        tahun_pilihan = st.sidebar.slider(
            "Pilih Rentang Tahun:",
            min_value=min_tahun,
            max_value=max_tahun,
            value=(min_tahun, max_tahun)
        )

        # Terapkan filter pada dataframe
        df_filtered = df[
            (df['Kota'].isin(kota_pilihan)) & 
            (df['Tahun'] >= tahun_pilihan[0]) & 
            (df['Tahun'] <= tahun_pilihan[1])
        ]

        if df_filtered.empty:
            st.warning("Data tidak tersedia untuk filter yang dipilih.")
        else:
            st.markdown("Visualisasi data alokasi dana, belanja modal, serta indikator sosial dan ekonomi daerah.")
            
            # --- Row 1: Key Metrics (Rata-rata pada rentang waktu terpilih) ---
            st.subheader("Indikator Makro (Rata-rata)")
            col1, col2, col3, col4 = st.columns(4)
            
            # Menggunakan get() untuk menghindari error jika kolom tidak ada
            avg_pe = df_filtered.get('PE', pd.Series([0])).mean()
            avg_ipm = df_filtered.get('IPM', pd.Series([0])).mean()
            avg_kemiskinan = df_filtered.get('KEMISKINAN', pd.Series([0])).mean()
            avg_pengangguran = df_filtered.get('PENGANGGURAN', pd.Series([0])).mean()
            
            col1.metric("Pertumbuhan Ekonomi (PE)", f"{avg_pe:.2f}%")
            col2.metric("Indeks Pembangunan Manusia (IPM)", f"{avg_ipm:.2f}")
            col3.metric("Tingkat Kemiskinan", f"{avg_kemiskinan:.2f}%")
            col4.metric("Tingkat Pengangguran", f"{avg_pengangguran:.2f}%")

            st.divider()

            # --- Row 2: Trend Ekonomi & IPM ---
            col1, col2 = st.columns(2)
            with col1:
                if 'PE' in df_filtered.columns:
                    fig_pe = px.line(
                        df_filtered, x='Tahun', y='PE', color='Kota', markers=True,
                        title='Tren Pertumbuhan Ekonomi (PE) per Tahun'
                    )
                    st.plotly_chart(fig_pe, use_container_width=True)

            with col2:
                if 'IPM' in df_filtered.columns:
                    fig_ipm = px.line(
                        df_filtered, x='Tahun', y='IPM', color='Kota', markers=True,
                        title='Tren Indeks Pembangunan Manusia (IPM) per Tahun'
                    )
                    st.plotly_chart(fig_ipm, use_container_width=True)

            # --- Row 3: Trend Kemiskinan & Pendapatan Asli Daerah (PAD) ---
            col1, col2 = st.columns(2)
            with col1:
                if 'KEMISKINAN' in df_filtered.columns:
                    fig_kemiskinan = px.bar(
                        df_filtered, x='Tahun', y='KEMISKINAN', color='Kota', barmode='group',
                        title='Perbandingan Tingkat Kemiskinan'
                    )
                    st.plotly_chart(fig_kemiskinan, use_container_width=True)

            with col2:
                if 'PAD' in df_filtered.columns:
                    fig_pad = px.line(
                        df_filtered, x='Tahun', y='PAD', color='Kota', markers=True,
                        title='Tren Pendapatan Asli Daerah (PAD)'
                    )
                    st.plotly_chart(fig_pad, use_container_width=True)

            # --- Row 4: Distribusi Belanja Modal ---
            st.subheader("Distribusi Belanja Modal")
            
            # Mengambil kolom belanja modal yang ada di dataset
            bm_columns = [col for col in df_filtered.columns if col.startswith('bm_')]
            
            if bm_columns:
                df_bm = df_filtered.groupby('Kota')[bm_columns].mean().reset_index()
                df_bm_melted = df_bm.melt(id_vars='Kota', value_vars=bm_columns, 
                                          var_name='Kategori Belanja', value_name='Nilai')
                
                df_bm_melted['Kategori Belanja'] = df_bm_melted['Kategori Belanja'].str.replace('bm_', '').str.replace('_', ' ').str.title()

                fig_bm = px.bar(
                    df_bm_melted, x='Kota', y='Nilai', color='Kategori Belanja',
                    title='Rata-rata Komposisi Belanja Modal Daerah',
                    barmode='stack'
                )
                st.plotly_chart(fig_bm, use_container_width=True)
            else:
                st.info("Tidak ada kolom belanja modal (diawali dengan 'bm_') ditemukan di dataset.")

            # --- Row 5: Scatter Plot PE vs Kemiskinan ---
            if all(col in df_filtered.columns for col in ['PE', 'KEMISKINAN', 'IPM']):
                st.subheader("Korelasi Ekonomi & Kemiskinan")
                fig_scatter = px.scatter(
                    df_filtered, x='PE', y='KEMISKINAN', color='Kota', size='IPM', 
                    hover_data=['Tahun'],
                    title='Pertumbuhan Ekonomi vs Kemiskinan (Ukuran Bubble = IPM)'
                )
                st.plotly_chart(fig_scatter, use_container_width=True)

            # --- Data Tabel ---
            with st.expander("Lihat Detail Data Tabular"):
                st.dataframe(df_filtered)
    else:
        st.error("Dataset harus memiliki kolom 'Kota' dan 'Tahun' untuk dapat menggunakan dashboard ini.")
        st.dataframe(df) # Tetap tampilkan datanya agar user bisa mengecek nama kolomnya

else:
    # Tampilan awal sebelum file diunggah
    st.info("👋 Selamat datang! Silakan unggah file CSV Anda (seperti **dataset_fiskal_97_hipoFull.csv**) di menu sebelah kiri (sidebar) untuk mulai memvisualisasikan data.")