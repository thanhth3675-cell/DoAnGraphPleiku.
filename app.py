import streamlit as st
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
import osmnx as ox
import folium
from folium.plugins import AntPath # Thư viện tạo hiệu ứng đường đi chuyển động
from streamlit_folium import st_folium
import warnings

# Tắt cảnh báo để giao diện sạch đẹp
warnings.filterwarnings("ignore")

# -----------------------------------------------------------------------------
# 1. CẤU HÌNH & KHỞI TẠO
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Đồ Án Đồ Thị & Pleiku Map", layout="wide", page_icon="🕸️")

st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; height: 3em; }
    h1 { color: #2E86C1; text-align: center; font-family: 'Segoe UI', sans-serif; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #f0f2f6; border-radius: 5px; }
    .stTabs [aria-selected="true"] { background-color: #D6EAF8; font-weight: bold; color: #2874A6; }
    .result-card { padding: 15px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .dijkstra { background-color: #EBF5FB; border-left: 5px solid #3498DB; color: #2874A6; }
    .bfs { background-color: #F4ECF7; border-left: 5px solid #8E44AD; color: #6C3483; }
    .dfs { background-color: #FEF9E7; border-left: 5px solid #F1C40F; color: #9A7D0A; }
    </style>
    """, unsafe_allow_html=True)

# Khởi tạo Session State (Bộ nhớ tạm)
if 'G' not in st.session_state:
    st.session_state['G'] = nx.Graph()
if 'path_nodes' not in st.session_state: st.session_state['path_nodes'] = []
if 'path_info' not in st.session_state: st.session_state['path_info'] = {}
if 'map_center' not in st.session_state: st.session_state['map_center'] = [13.9785, 108.0051]

# -----------------------------------------------------------------------------
# 2. HÀM VẼ ĐỒ THỊ LÝ THUYẾT (TAB 1)
# -----------------------------------------------------------------------------
def draw_graph_theory(graph, path_nodes=None, path_edges=None, title="Trực quan hóa"):
    fig, ax = plt.subplots(figsize=(10, 6))
    pos = nx.spring_layout(graph, seed=42)
    
    # Vẽ nền
    nx.draw_networkx_nodes(graph, pos, node_size=700, node_color="#AED6F1", ax=ax)
    nx.draw_networkx_edges(graph, pos, width=2, alpha=0.5, edge_color="gray", ax=ax)
    nx.draw_networkx_labels(graph, pos, font_size=12, font_weight="bold", ax=ax)
    edge_labels = nx.get_edge_attributes(graph, 'weight')
    nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels, font_size=10, ax=ax)

    # Highlight (Đường đi hoặc MST)
    if path_nodes:
        nx.draw_networkx_nodes(graph, pos, nodelist=path_nodes, node_color="#E74C3C", node_size=800, ax=ax)
        # Tạo danh sách cạnh từ các node liền kề
        if len(path_nodes) > 1:
            path_edges_list = list(zip(path_nodes, path_nodes[1:]))
            nx.draw_networkx_edges(graph, pos, edgelist=path_edges_list, width=4, edge_color="#E74C3C", ax=ax)
            
    if path_edges: # Dùng cho Prim
        nx.draw_networkx_edges(graph, pos, edgelist=path_edges, width=4, edge_color="#27AE60", ax=ax)
    
    ax.set_title(title, fontsize=14, color="#2874A6")
    ax.axis('off')
    st.pyplot(fig)

# -----------------------------------------------------------------------------
# 3. GIAO DIỆN CHÍNH
# -----------------------------------------------------------------------------
st.title("🕸️ ỨNG DỤNG MÔ PHỎNG THUẬT TOÁN ĐỒ THỊ")

tab_theory, tab_map = st.tabs(["📚 PHẦN 1: LÝ THUYẾT (FULL 7 YÊU CẦU)", "🗺️ PHẦN 2: BẢN ĐỒ PLEIKU (NÂNG CAO)"])

# =============================================================================
# TAB 1: LÝ THUYẾT
# =============================================================================
with tab_theory:
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("1. Nhập liệu")
        # YC 6: Hướng/Vô hướng
        type_opt = st.radio("Loại đồ thị:", ["Vô hướng", "Có hướng"])
        is_directed = "Có hướng" in type_opt
        
        # YC 6: Nhập cạnh
        default_val = "A B 4\nA C 2\nB C 5\nB D 10\nC E 3\nD F 11\nE D 4"
        inp = st.text_area("Danh sách cạnh (u v w):", value=default_val, height=150)
        
        # YC 1: Tạo & Vẽ
        if st.button("🚀 Tạo Đồ Thị (YC1)"):
            try:
                G = nx.DiGraph() if is_directed else nx.Graph()
                for line in inp.strip().split('\n'):
                    parts = line.split()
                    if len(parts) >= 2:
                        w = int(parts[2]) if len(parts) > 2 else 1
                        G.add_edge(parts[0], parts[1], weight=w)
                st.session_state['G'] = G
                st.success("Đã tạo xong!")
            except: st.error("Lỗi dữ liệu nhập!")

        # YC 2: Lưu
        st.download_button("💾 Lưu đồ thị (.txt)", inp, "graph.txt")

    with c2:
        G = st.session_state['G']
        if len(G) > 0: draw_graph_theory(G, title="Mô hình Đồ thị")
        else: st.info("👈 Vui lòng nhập dữ liệu.")

    if len(G) > 0:
        st.divider()
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("##### 🛠️ Biểu diễn")
            # YC 6: Chuyển đổi
            mode = st.selectbox("Xem dạng:", ["Ma trận kề", "Danh sách kề"])
            if mode == "Ma trận kề":
                st.dataframe(pd.DataFrame(nx.adjacency_matrix(G).todense(), index=G.nodes(), columns=G.nodes()), height=150)
            else: st.json(nx.to_dict_of_lists(G), expanded=False)
            
            # YC 5: Kiểm tra 2 phía
            if st.button("Kiểm tra 2 phía"):
                st.write(f"Kết quả: {'✅ Có' if nx.is_bipartite(G) else '❌ Không'}")

        with col2:
            st.markdown("##### 🔍 Duyệt & Tìm đường")
            start = st.selectbox("Start:", list(G.nodes()))
            end = st.selectbox("End:", list(G.nodes()), index=len(G.nodes())-1)
            
            # YC 4: BFS/DFS
            b1, b2 = st.columns(2)
            with b1:
                if st.button("BFS"):
                    # BFS Tree traversal
                    path = list(dict(nx.bfs_successors(G, start)).keys()); path.insert(0, start)
                    st.success(f"BFS: {path}"); draw_graph_theory(G, path_nodes=path, title="BFS")
            with b2:
                if st.button("DFS"):
                    # DFS Preorder traversal
                    path = list(nx.dfs_preorder_nodes(G, start))
                    st.success(f"DFS: {path}"); draw_graph_theory(G, path_nodes=path, title="DFS")
            
            # YC 3: Dijkstra
            if st.button("Dijkstra"):
                try:
                    p = nx.shortest_path(G, start, end, weight='weight')
                    w = nx.shortest_path_length(G, start, end, weight='weight')
                    st.success(f"Path: {p} (W={w})")
                    draw_graph_theory(G, path_nodes=p, title="Shortest Path")
                except: st.error("Không có đường đi")

        with col3:
            st.markdown("##### 🌲 Nâng cao")
            # YC 7: Prim
            if st.button("Prim (MST)"):
                if not is_directed and nx.is_connected(G):
                    mst = nx.minimum_spanning_tree(G, algorithm='prim')
                    st.info(f"Tổng W: {mst.size(weight='weight')}")
                    draw_graph_theory(G, path_edges=list(mst.edges()), title="MST Prim")
                else: st.warning("Chỉ chạy với đồ thị vô hướng liên thông.")

# =============================================================================
# TAB 2: BẢN ĐỒ PLEIKU (CÓ HIỆU ỨNG CHUYỂN ĐỘNG)
# =============================================================================
with tab_map:
    st.header("🗺️ Tìm đường thông minh tại TP. Pleiku")

    # 1. LOAD MAP (Bán kính 3km)
    @st.cache_resource
    def load_pleiku_map():
        point = (13.9785, 108.0051)
        # Sử dụng network_type='drive' cho đường xe chạy
        return ox.graph_from_point(point, dist=3000, network_type='drive')

    with st.spinner("Đang tải dữ liệu bản đồ Pleiku (Chỉ mất vài giây)..."):
        try:
            G_map = load_pleiku_map()
            st.success(f"✅ Đã tải xong! Sẵn sàng tìm đường.")
        except Exception as e:
            st.error(f"Lỗi tải map: {e}")
            st.stop()

    # 2. ĐỊA ĐIỂM
    locations = {
        "Quảng trường Đại Đoàn Kết": (13.9785, 108.0051),
        "Sân vận động Pleiku": (13.9791, 108.0076),
        "Chợ Đêm Pleiku": (13.9745, 108.0068),
        "Vincom Plaza": (13.9804, 108.0053),
        "Coop Mart Pleiku": (13.9818, 108.0064),
        "Bệnh viện Đa khoa Tỉnh": (13.9822, 108.0019),
        "Công viên Diên Hồng": (13.9715, 108.0022),
        "Bưu điện Tỉnh": (13.9770, 108.0040),
        "Khách sạn Hoàng Anh Gia Lai": (13.9760, 108.0030),
        "Khách sạn Tre Xanh": (13.9790, 108.0060),
        "Ngã 3 Hoa Lư": (13.9850, 108.0050),
        "Sân bay Pleiku (Hơi xa)": (13.9963, 108.0142)
    }

    c1, c2, c3 = st.columns([1.8, 1.8, 1.5])
    start_name = c1.selectbox("📍 Điểm đi:", list(locations.keys()), index=0)
    end_name = c2.selectbox("🏁 Điểm đến:", list(locations.keys()), index=6)
    algo_choice = c3.selectbox("Thuật toán:", ["Dijkstra (Tối ưu)", "BFS (Ít rẽ)", "DFS (Demo)"])
    
    if st.button("🚀 TÌM ĐƯỜNG NGAY", type="primary"):
        try:
            u_coord, v_coord = locations[start_name], locations[end_name]
            orig = ox.distance.nearest_nodes(G_map, u_coord[1], u_coord[0])
            dest = ox.distance.nearest_nodes(G_map, v_coord[1], v_coord[0])

            path = []
            info = {}
            
            if "Dijkstra" in algo_choice:
                path = nx.shortest_path(G_map, orig, dest, weight='length')
                d = nx.shortest_path_length(G_map, orig, dest, weight='length')
                info = {"msg": f"🔵 Dijkstra: Quãng đường ngắn nhất: {d/1000:.2f} km", "style": "dijkstra", "color": "#3498DB"}
            
            elif "BFS" in algo_choice:
                path = nx.shortest_path(G_map, orig, dest, weight=None)
                info = {"msg": f"🟣 BFS: Lộ trình qua {len(path)} giao lộ (Ưu tiên ít rẽ nhất)", "style": "bfs", "color": "#8E44AD"}
            
            elif "DFS" in algo_choice:
                try: path = next(nx.all_simple_paths(G_map, orig, dest, cutoff=80))
                except: path = []
                info = {"msg": "🟠 DFS: Đã tìm thấy một đường đi (Mang tính minh họa thuật toán)", "style": "dfs", "color": "#F1C40F"}

            # Lưu vào Session
            st.session_state['path_nodes'] = path
            st.session_state['path_info'] = info
            st.session_state['map_center'] = [(u_coord[0]+v_coord[0])/2, (u_coord[1]+v_coord[1])/2]

        except Exception as e:
            st.error(f"Lỗi: {e}")

    # HIỂN THỊ KẾT QUẢ
    info = st.session_state['path_info']
    if info:
        st.markdown(f"<div class='result-card {info['style']}'><h4>{info['msg']}</h4></div>", unsafe_allow_html=True)

    # VẼ BẢN ĐỒ
    m = folium.Map(location=st.session_state['map_center'], zoom_start=14, tiles="OpenStreetMap")
    
    # Marker Điểm đi/đến
    folium.Marker(locations[start_name], popup=f"Start: {start_name}", icon=folium.Icon(color="green", icon="play"), tooltip="Điểm đi").add_to(m)
    folium.Marker(locations[end_name], popup=f"End: {end_name}", icon=folium.Icon(color="red", icon="flag"), tooltip="Điểm đến").add_to(m)

    # VẼ ĐƯỜNG ĐI CÓ HIỆU ỨNG (ANTPATH)
    path = st.session_state['path_nodes']
    if path:
        # Lấy tọa độ đường đi
        route_coords = [(G_map.nodes[n]['y'], G_map.nodes[n]['x']) for n in path]
        
        # Dùng AntPath thay vì PolyLine thường -> Tạo hiệu ứng kiến bò
        AntPath(
            locations=route_coords,
            color=info['color'], # Màu theo thuật toán
            weight=6,
            opacity=0.8,
            delay=1000,      # Tốc độ chạy
            pulse_color='#FFFFFF', # Màu vạch chạy (trắng)
            tooltip=f"Lộ trình: {algo_choice}",
            popup=info['msg']
        ).add_to(m)

    st_folium(m, width=1000, height=500)
