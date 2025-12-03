import streamlit as st
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import osmnx as ox
import folium
from streamlit_folium import st_folium

# -----------------------------------------------------------------------------
# 1. CẤU HÌNH & KHỞI TẠO
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Đồ Án: Lý Thuyết & Ứng Dụng Đồ Thị", layout="wide", page_icon="🕸️")

# CSS làm đẹp giao diện
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; font-weight: bold; }
    h1 { color: #2E86C1; text-align: center; }
    h3 { color: #117A65; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #f0f2f6; border-radius: 5px; }
    .stTabs [aria-selected="true"] { background-color: #D6EAF8; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# Khởi tạo Session State (Bộ nhớ)
if 'G' not in st.session_state:
    st.session_state['G'] = nx.Graph()
if 'graph_type' not in st.session_state:
    st.session_state['graph_type'] = "Vô hướng"

# -----------------------------------------------------------------------------
# 2. HÀM VẼ ĐỒ THỊ (Dùng cho Tab Lý Thuyết)
# -----------------------------------------------------------------------------
def draw_graph(graph, path_nodes=None, path_edges=None, title="Trực quan hóa", node_color="#85C1E9"):
    """
    Hàm vẽ đồ thị đa năng: Hỗ trợ tô màu node, tô màu cạnh (cho Prim/Path).
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Layout lò xo cố định để hình không bị nhảy lung tung
    pos = nx.spring_layout(graph, seed=42) 
    
    # 1. Vẽ Node & Edge cơ bản
    nx.draw_networkx_nodes(graph, pos, node_size=700, node_color=node_color, ax=ax)
    nx.draw_networkx_edges(graph, pos, width=2, alpha=0.3, edge_color="gray", ax=ax)
    nx.draw_networkx_labels(graph, pos, font_size=12, font_weight="bold", font_color="black", ax=ax)
    
    # 2. Vẽ trọng số
    edge_labels = nx.get_edge_attributes(graph, 'weight')
    nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels, font_size=10, ax=ax)

    # 3. Highlight (Nếu có yêu cầu vẽ đường đi hoặc cây khung)
    if path_nodes: # Tô màu các node trong danh sách
        nx.draw_networkx_nodes(graph, pos, nodelist=path_nodes, node_color="#FF5733", node_size=800, ax=ax)
    
    if path_edges: # Tô màu các cạnh (Dùng cho Prim hoặc Đường đi)
        nx.draw_networkx_edges(graph, pos, edgelist=path_edges, width=4, edge_color="#FF5733", ax=ax)

    ax.set_title(title, fontsize=14, color="#BA4A00")
    ax.axis('off')
    st.pyplot(fig)

# -----------------------------------------------------------------------------
# 3. GIAO DIỆN CHÍNH
# -----------------------------------------------------------------------------
st.title("🕸️ ỨNG DỤNG MÔ PHỎNG THUẬT TOÁN ĐỒ THỊ")
st.write("Bài tập lớn: Tích hợp Lý thuyết đồ thị và Bản đồ thực tế TP. Pleiku.")

tab_theory, tab_map = st.tabs(["📚 PHẦN 1: LÝ THUYẾT (7 YÊU CẦU)", "🗺️ PHẦN 2: BẢN ĐỒ PLEIKU (NÂNG CAO)"])

# =============================================================================
# TAB 1: GIẢI QUYẾT 7 YÊU CẦU LÝ THUYẾT
# =============================================================================
with tab_theory:
    # --- CỘT TRÁI: NHẬP LIỆU (Yêu cầu 6 - Danh sách cạnh) ---
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("1. Nhập liệu")
        # Chọn loại đồ thị (Vô hướng / Có hướng)
        type_opt = st.radio("Loại đồ thị:", ["Vô hướng", "Có hướng"])
        is_directed = "Có hướng" in type_opt
        
        # Input Text
        default_txt = "A B 4\nA C 2\nB C 5\nB D 10\nC E 3\nD F 11\nE D 4"
        inp = st.text_area("Nhập Danh sách cạnh (u v w):", value=default_txt, height=200)

        # Nút Tạo Đồ Thị
        if st.button("🚀 Tạo & Vẽ Đồ Thị (YC 1)"):
            try:
                new_G = nx.DiGraph() if is_directed else nx.Graph()
                for line in inp.strip().split('\n'):
                    parts = line.split()
                    if len(parts) >= 2:
                        u, v = parts[0], parts[1]
                        w = int(parts[2]) if len(parts) > 2 else 1
                        new_G.add_edge(u, v, weight=w)
                st.session_state['G'] = new_G
                st.session_state['graph_type'] = type_opt
                st.success("Đã cập nhật dữ liệu!")
            except Exception as e: st.error(f"Lỗi nhập liệu: {e}")
        
        # [Yêu cầu 2] Lưu đồ thị
        st.download_button("💾 Lưu đồ thị (YC 2)", inp, "graph_data.txt")

    # --- CỘT PHẢI: TRỰC QUAN HÓA (Yêu cầu 1) ---
    with c2:
        G = st.session_state['G']
        if G.number_of_nodes() > 0:
            draw_graph(G, title=f"Đồ thị hiện tại ({st.session_state['graph_type']})")
        else:
            st.info("👈 Vui lòng nhập dữ liệu và bấm 'Tạo Đồ Thị'.")

    st.divider()

    # --- KHU VỰC CHỨC NĂNG (Yêu cầu 3, 4, 5, 6, 7) ---
    if G.number_of_nodes() > 0:
        col_A, col_B, col_C = st.columns(3)

        # --- CỘT A: BIỂU DIỄN & TÍNH CHẤT ---
        with col_A:
            st.markdown("#### 🛠️ Biểu diễn & Tính chất")
            
            # [Yêu cầu 6] Chuyển đổi biểu diễn
            st.write("**Chuyển đổi biểu diễn (YC 6):**")
            rep_type = st.selectbox("Chọn dạng xem:", ["Ma trận kề", "Danh sách kề"])
            if rep_type == "Ma trận kề":
                df = pd.DataFrame(nx.adjacency_matrix(G).todense(), index=G.nodes(), columns=G.nodes())
                st.dataframe(df, height=150)
            else:
                st.json(nx.to_dict_of_lists(G), expanded=False)

            # [Yêu cầu 5] Kiểm tra 2 phía
            st.write("**Kiểm tra tính chất (YC 5):**")
            if st.button("Kiểm tra Đồ thị 2 phía"):
                if nx.is_bipartite(G):
                    st.success("✅ ĐÚNG. Đây là đồ thị 2 phía.")
                    st.json(nx.bipartite.color(G)) # Show màu
                else:
                    st.error("❌ SAI. Không phải đồ thị 2 phía.")

        # --- CỘT B: DUYỆT & TÌM ĐƯỜNG ---
        with col_B:
            st.markdown("#### 🔍 Duyệt & Tìm đường")
            start = st.selectbox("Điểm bắt đầu:", list(G.nodes()))
            end = st.selectbox("Điểm kết thúc:", list(G.nodes()), index=len(G.nodes())-1)

            # [Yêu cầu 4] BFS & DFS
            c_bfs, c_dfs = st.columns(2)
            with c_bfs:
                if st.button("BFS (YC 4)"):
                    path = list(dict(nx.bfs_successors(G, start)).keys()) # Lấy các node duyệt được
                    path.insert(0, start)
                    st.success(f"BFS: {path}")
                    draw_graph(G, path_nodes=path, title=f"Duyệt BFS từ {start}")
            with c_dfs:
                if st.button("DFS (YC 4)"):
                    path = list(nx.dfs_preorder_nodes(G, start))
                    st.success(f"DFS: {path}")
                    draw_graph(G, path_nodes=path, title=f"Duyệt DFS từ {start}")

            # [Yêu cầu 3] Đường đi ngắn nhất
            st.write("---")
            if st.button("Tìm đường ngắn nhất (YC 3)"):
                try:
                    p = nx.shortest_path(G, start, end, weight='weight')
                    w = nx.shortest_path_length(G, start, end, weight='weight')
                    st.success(f"Dijkstra: {p} (Tổng trọng số: {w})")
                    # Vẽ Highlight đường đi
                    edges_path = list(zip(p, p[1:]))
                    draw_graph(G, path_nodes=p, path_edges=edges_path, title=f"Đường đi ngắn nhất: {start} -> {end}")
                except: st.error("Không có đường đi!")

        # --- CỘT C: THUẬT TOÁN NÂNG CAO (PRIM) ---
        with col_C:
            st.markdown("#### 🌲 Nâng cao (Prim)")
            
            # [Yêu cầu 7] Prim
            st.write("**(YC 7.1) Thuật toán Prim (MST):**")
            if is_directed:
                st.warning("⚠️ Prim chỉ áp dụng cho đồ thị Vô Hướng. Hãy chọn lại loại đồ thị ở bước 1.")
            else:
                if st.button("Chạy Prim Visualizer"):
                    if nx.is_connected(G):
                        # Tính cây khung
                        mst = nx.minimum_spanning_tree(G, algorithm='prim')
                        total_w = mst.size(weight='weight')
                        st.info(f"Tổng trọng số cây khung: **{total_w}**")
                        
                        # Highlight các cạnh thuộc MST
                        mst_edges = list(mst.edges())
                        mst_nodes = list(mst.nodes())
                        draw_graph(G, path_nodes=mst_nodes, path_edges=mst_edges, title="Cây khung nhỏ nhất (Prim)")
                    else:
                        st.error("Đồ thị không liên thông, không thể chạy Prim.")

# =============================================================================
# TAB 2: BẢN ĐỒ PLEIKU (PHIÊN BẢN TỐI ƯU V3)
# =============================================================================
with tab_map:
    st.header("🗺️ Tìm đường tại TP. Pleiku (Trung tâm)")

    # 1. LOAD MAP: Chỉ tải bán kính 5km từ Quảng trường (Nhẹ & Nhanh)
    @st.cache_resource
    def load_pleiku_map():
        # Tọa độ Quảng trường Đại Đoàn Kết
        center_point = (13.9785, 108.0051)
        G = ox.graph_from_point(center_point, dist=5000, network_type='drive')
        return G

    with st.spinner("Đang tải bản đồ Pleiku (Bán kính 5km)..."):
        try:
            G_map = load_pleiku_map()
            st.success(f"✅ Đã tải xong! Bản đồ gồm {len(G_map.nodes)} giao lộ.")
        except Exception as e:
            st.error(f"Lỗi tải bản đồ: {e}")
            st.stop()

    # 2. DANH SÁCH 30 ĐỊA ĐIỂM (CÓ TỌA ĐỘ)
    locations = {
        "Quảng trường Đại Đoàn Kết": (13.9785, 108.0051),
        "Sân bay Pleiku": (13.9963, 108.0142),
        "Biển Hồ (Tơ Nưng)": (14.0534, 108.0035),
        "Bến xe Đức Long": (13.9556, 108.0264),
        "Sân vận động Pleiku": (13.9791, 108.0076),
        "Chợ Đêm Pleiku": (13.9745, 108.0068),
        "TTTM Vincom Plaza": (13.9804, 108.0053),
        "Coop Mart Pleiku": (13.9818, 108.0064),
        "Bệnh viện Đa khoa Tỉnh": (13.9822, 108.0019),
        "Bệnh viện ĐH Y Dược HAGL": (13.9700, 108.0000),
        "Bệnh viện Nhi Gia Lai": (13.9600, 108.0100),
        "Công viên Diên Hồng": (13.9715, 108.0022),
        "Chùa Minh Thành": (13.9680, 108.0100),
        "Nhà thờ Đức An": (13.9750, 108.0050),
        "Bưu điện Tỉnh Gia Lai": (13.9770, 108.0040),
        "Trường THPT Chuyên Hùng Vương": (13.9850, 108.0100),
        "Trường THPT Pleiku": (13.9800, 108.0120),
        "Trường CĐ Sư phạm Gia Lai": (13.9600, 108.0200),
        "Khách sạn Hoàng Anh Gia Lai": (13.9760, 108.0030),
        "Khách sạn Tre Xanh": (13.9790, 108.0060),
        "Khách sạn Khánh Linh": (13.9780, 108.0050),
        "Khách sạn Mê Kông": (13.9750, 108.0020),
        "Công an Tỉnh Gia Lai": (13.9780, 108.0020),
        "Ủy ban Nhân dân Tỉnh": (13.9790, 108.0040),
        "Ngã 3 Hoa Lư": (13.9850, 108.0050),
        "Ngã 4 Biển Hồ": (14.0000, 108.0000),
        "Chợ Trung tâm Pleiku": (13.9750, 108.0080),
        "Bảo tàng Tỉnh Gia Lai": (13.9780, 108.0055),
        "Rạp chiếu phim Touch Cinema": (13.9700, 108.0100),
        "Công viên Đồng Xanh": (13.9800, 108.0500)
    }

    # 3. GIAO DIỆN CHỌN
    col_s1, col_s2, col_algo = st.columns([1.5, 1.5, 1.5])
    with col_s1:
        start_name = st.selectbox("📍 Điểm Xuất Phát:", list(locations.keys()), index=0)
    with col_s2:
        end_name = st.selectbox("🏁 Điểm Đến:", list(locations.keys()), index=1)
    with col_algo:
        algo_choice = st.selectbox("Thuật toán:", 
                                   ["Dijkstra (Đường ngắn nhất)", 
                                    "BFS (Ít ngã rẽ nhất)", 
                                    "DFS (Duyệt chiều sâu - Demo)"])
    
    btn_run = st.button("🚀 TÌM ĐƯỜNG TRÊN BẢN ĐỒ", type="primary")

    # 4. XỬ LÝ & VẼ MAP
    start_coords = locations[start_name]
    end_coords = locations[end_name]

    # Tìm node gần nhất trên đồ thị
    try:
        orig_node = ox.distance.nearest_nodes(G_map, start_coords[1], start_coords[0])
        dest_node = ox.distance.nearest_nodes(G_map, end_coords[1], end_coords[0])
    except:
        orig_node = list(G_map.nodes())[0] # Fallback

    # Tạo Map nền Folium
    mid_lat = (start_coords[0] + end_coords[0]) / 2
    mid_lon = (start_coords[1] + end_coords[1]) / 2
    m = folium.Map(location=[mid_lat, mid_lon], zoom_start=14, tiles="OpenStreetMap")
    
    folium.Marker(start_coords, popup=f"Start: {start_name}", icon=folium.Icon(color="green", icon="play")).add_to(m)
    folium.Marker(end_coords, popup=f"End: {end_name}", icon=folium.Icon(color="red", icon="flag")).add_to(m)

    if btn_run:
        path = []
        try:
            if "Dijkstra" in algo_choice:
                # Dijkstra: weight='length'
                path = nx.shortest_path(G_map, orig_node, dest_node, weight='length')
                dist = nx.shortest_path_length(G_map, orig_node, dest_node, weight='length')
                st.success(f"🔵 **Dijkstra:** Đường ngắn nhất dài **{dist/1000:.2f} km**.")
                color_path = "blue"
            
            elif "BFS" in algo_choice:
                # BFS: weight=None
                path = nx.shortest_path(G_map, orig_node, dest_node, weight=None)
                st.info(f"🟣 **BFS:** Tìm thấy đường đi qua **{len(path)}** giao lộ.")
                color_path = "purple"

            elif "DFS" in algo_choice:
                # DFS: Demo
                try:
                    path = next(nx.all_simple_paths(G_map, orig_node, dest_node, cutoff=100))
                except:
                    path = list(nx.dfs_preorder_nodes(G_map, source=orig_node))
                    if dest_node in path:
                        path = path[:path.index(dest_node)+1]
                    else: path = []
                st.warning(f"🟠 **DFS:** Đã tìm thấy đường (Mang tính minh họa).")
                color_path = "orange"

            # Vẽ đường
            if path:
                ox.plot_route_folium(G_map, path, m, color=color_path, weight=6, opacity=0.8)
            
        except nx.NetworkXNoPath:
            st.error("🚫 Không có đường đi giữa 2 địa điểm này.")
        except Exception as e:
            st.error(f"Lỗi: {e}")

    # Hiển thị Map
    st_folium(m, width=1400, height=600)
