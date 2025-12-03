import streamlit as st
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
import osmnx as ox
import folium
from folium.plugins import AntPath
from streamlit_folium import st_folium
import warnings

# Tắt cảnh báo
warnings.filterwarnings("ignore")

# 1. CẤU HÌNH GIAO DIỆN
st.set_page_config(page_title="Đồ Án Đồ Thị & Pleiku Map", layout="wide", page_icon="🗺️")

st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; height: 3em; }
    h1 { color: #2E86C1; text-align: center; font-family: 'Segoe UI'; }
    .route-step { 
        padding: 12px; margin-bottom: 8px; background-color: white; 
        border-left: 5px solid #3498DB; border-radius: 4px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1); display: flex;
        justify-content: space-between; align-items: center;
    }
    .step-name { font-weight: bold; color: #2C3E50; }
    .step-dist { font-weight: bold; color: #E74C3C; font-size: 0.9em; background: #FDEDEC; padding: 4px 8px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# Khởi tạo Session
if 'G' not in st.session_state: st.session_state['G'] = nx.Graph()
if 'graph_type' not in st.session_state: st.session_state['graph_type'] = "Vô hướng"
if 'path_nodes' not in st.session_state: st.session_state['path_nodes'] = []
if 'path_detail' not in st.session_state: st.session_state['path_detail'] = []
if 'map_center' not in st.session_state: st.session_state['map_center'] = [13.9785, 108.0051]

# -----------------------------------------------------------------------------
# HÀM XỬ LÝ LỘ TRÌNH CHI TIẾT
# -----------------------------------------------------------------------------
def get_turn_by_turn(G, path_nodes):
    if not path_nodes or len(path_nodes) < 2: return []
    segments = []
    curr_name = None
    curr_dist = 0
    
    for u, v in zip(path_nodes[:-1], path_nodes[1:]):
        edge = G.get_edge_data(u, v)[0]
        length = edge.get('length', 0)
        name = edge.get('name', 'Đường nội bộ')
        if isinstance(name, list): name = " / ".join(name)
        
        if name == curr_name:
            curr_dist += length
        else:
            if curr_name: segments.append({"name": curr_name, "dist": curr_dist})
            curr_name = name
            curr_dist = length
    if curr_name: segments.append({"name": curr_name, "dist": curr_dist})
    return segments

# -----------------------------------------------------------------------------
# HÀM VẼ LÝ THUYẾT (TAB 1)
# -----------------------------------------------------------------------------
def draw_graph_theory(graph, path_nodes=None, path_edges=None, title="Đồ thị"):
    fig, ax = plt.subplots(figsize=(10, 6))
    pos = nx.spring_layout(graph, seed=42)
    nx.draw_networkx_nodes(graph, pos, node_size=700, node_color="#AED6F1", ax=ax)
    nx.draw_networkx_edges(graph, pos, width=2, alpha=0.5, edge_color="gray", ax=ax)
    nx.draw_networkx_labels(graph, pos, font_size=12, font_weight="bold", ax=ax)
    nx.draw_networkx_edge_labels(graph, pos, edge_labels=nx.get_edge_attributes(graph, 'weight'), font_size=10, ax=ax)
    
    if path_nodes:
        nx.draw_networkx_nodes(graph, pos, nodelist=path_nodes, node_color="#E74C3C", node_size=800, ax=ax)
        if len(path_nodes) > 1:
            edges = list(zip(path_nodes, path_nodes[1:]))
            nx.draw_networkx_edges(graph, pos, edgelist=edges, width=4, edge_color="#E74C3C", ax=ax)
    if path_edges:
        nx.draw_networkx_edges(graph, pos, edgelist=path_edges, width=4, edge_color="#27AE60", ax=ax)
    
    ax.set_title(title, fontsize=14, color="#2874A6"); ax.axis('off'); st.pyplot(fig)

# -----------------------------------------------------------------------------
# GIAO DIỆN CHÍNH
# -----------------------------------------------------------------------------
st.title("ỨNG DỤNG MÔ PHỎNG THUẬT TOÁN ĐỒ THỊ")
tab1, tab2 = st.tabs(["📚 PHẦN 1: LÝ THUYẾT", "🗺️ PHẦN 2: BẢN ĐỒ PLEIKU (CHÍNH XÁC CAO)"])

# --- TAB 1: LÝ THUYẾT ---
with tab1:
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("1. Nhập liệu")
        type_opt = st.radio("Loại:", ["Vô hướng", "Có hướng"])
        is_directed = "Có hướng" in type_opt
        inp = st.text_area("Cạnh (u v w):", value="A B 4\nA C 2\nB C 5\nB D 10\nC E 3\nD F 11\nE D 4", height=150)
        if st.button("🚀 Tạo Đồ Thị (YC1)"):
            G = nx.DiGraph() if is_directed else nx.Graph()
            try:
                for line in inp.strip().split('\n'):
                    p = line.split()
                    if len(p)>=2: G.add_edge(p[0], p[1], weight=int(p[2]) if len(p)>2 else 1)
                st.session_state['G'] = G; st.session_state['graph_type'] = type_opt
                st.success("Đã tạo xong!")
            except: st.error("Lỗi dữ liệu!")
        st.download_button("💾 Lưu đồ thị (YC2)", inp, "graph.txt")

    with c2:
        G = st.session_state['G']
        if len(G)>0: draw_graph_theory(G, title=f"Mô hình ({st.session_state['graph_type']})")
        else: st.info("👈 Nhập dữ liệu để bắt đầu.")

    if len(G)>0:
        st.divider(); col1, col2, col3 = st.columns(3)
        with col1:
            mode = st.selectbox("Dạng xem (YC6):", ["Ma trận kề", "Danh sách kề"])
            if mode == "Ma trận kề": st.dataframe(pd.DataFrame(nx.adjacency_matrix(G).todense(), index=G.nodes(), columns=G.nodes()), height=150)
            else: st.json(nx.to_dict_of_lists(G), expanded=False)
            if st.button("Kiểm tra 2 phía (YC5)"): st.write(f"Kết quả: {'✅ Có' if nx.is_bipartite(G) else '❌ Không'}")
        with col2:
            s = st.selectbox("Start:", list(G.nodes()))
            e = st.selectbox("End:", list(G.nodes()), index=len(G.nodes())-1)
            b1, b2 = st.columns(2)
            with b1: 
                if st.button("BFS (YC4)"): 
                    p=list(dict(nx.bfs_successors(G,s)).keys()); p.insert(0,s); st.success(f"BFS: {p}"); draw_graph_theory(G,path_nodes=p,title="BFS")
            with b2:
                if st.button("DFS (YC4)"): 
                    p=list(nx.dfs_preorder_nodes(G,s)); st.success(f"DFS: {p}"); draw_graph_theory(G,path_nodes=p,title="DFS")
            if st.button("Dijkstra (YC3)"):
                try: p=nx.shortest_path(G,s,e,weight='weight'); draw_graph_theory(G,path_nodes=p,title="Shortest Path")
                except: st.error("Không có đường")
        with col3:
            if st.button("Prim (YC7)"):
                if not is_directed and nx.is_connected(G):
                    mst=nx.minimum_spanning_tree(G,algorithm='prim'); st.info(f"Tổng W: {mst.size(weight='weight')}")
                    draw_graph_theory(G,path_edges=list(mst.edges()),title="MST Prim")
                else: st.warning("Chỉ chạy trên đồ thị vô hướng liên thông.")

# --- TAB 2: BẢN ĐỒ PLEIKU (FIX LỖI CẮT NGANG) ---
with tab2:
    st.header("🗺️ Tìm đường chi tiết (Uốn lượn theo mặt đường)")

    @st.cache_resource
    def load_pleiku_map():
        # Bán kính 4km - Bao trùm 50 điểm
        return ox.graph_from_point((13.9785, 108.0051), dist=4000, network_type='drive')

    with st.spinner("Đang tải dữ liệu bản đồ Pleiku..."):
        try: G_map = load_pleiku_map(); st.success("✅ Đã tải xong hệ thống giao thông!")
        except: st.error("Lỗi kết nối bản đồ"); st.stop()

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
        "Bệnh viện Mắt Cao Nguyên": (13.9650, 108.0150),
        "Công viên Diên Hồng": (13.9715, 108.0022),
        "Công viên Đồng Xanh": (13.9800, 108.0500),
        "Chùa Minh Thành": (13.9680, 108.0100),
        "Nhà thờ Đức An": (13.9750, 108.0050),
        "Bưu điện Tỉnh Gia Lai": (13.9770, 108.0040),
        "Trường THPT Chuyên Hùng Vương": (13.9850, 108.0100),
        "Trường THPT Pleiku": (13.9800, 108.0120),
        "Khách sạn Hoàng Anh Gia Lai": (13.9760, 108.0030),
        "Khách sạn Tre Xanh": (13.9790, 108.0060),
        "Khách sạn Khánh Linh": (13.9780, 108.0050),
        "Khách sạn Mê Kông": (13.9750, 108.0020),
        "Công an Tỉnh Gia Lai": (13.9780, 108.0020),
        "Ủy ban Nhân dân Tỉnh": (13.9790, 108.0040),
        "Bảo tàng Tỉnh Gia Lai": (13.9780, 108.0055),
        "Ngã 3 Hoa Lư": (13.9850, 108.0050),
        "Ngã 4 Biển Hồ": (14.0000, 108.0000),
        "Chợ Mới Pleiku": (13.9750, 108.0080),
        "Rạp Touch Cinema": (13.9700, 108.0100),
        "Học viện Bóng đá HAGL": (13.9500, 108.0500)
    }

    c1, c2, c3 = st.columns([2, 2, 1.5])
    start_name = c1.selectbox("📍 Điểm Xuất Phát:", sorted(locations.keys()), index=0)
    end_name = c2.selectbox("🏁 Điểm Đến:", sorted(locations.keys()), index=1)
    algo_choice = c3.selectbox("Thuật toán:", ["Dijkstra (Ngắn nhất)", "BFS (Ít rẽ nhất)", "DFS (Demo)"])
    
    if st.button("🚀 TÌM ĐƯỜNG CHI TIẾT", type="primary"):
        try:
            u, v = locations[start_name], locations[end_name]
            # Tìm node gần nhất
            orig = ox.distance.nearest_nodes(G_map, u[1], u[0])
            dest = ox.distance.nearest_nodes(G_map, v[1], v[0])
            
            path = []
            if "Dijkstra" in algo_choice: path = nx.shortest_path(G_map, orig, dest, weight='length')
            elif "BFS" in algo_choice: path = nx.shortest_path(G_map, orig, dest, weight=None)
            elif "DFS" in algo_choice: 
                try: path = next(nx.all_simple_paths(G_map, orig, dest, cutoff=100))
                except: path = []

            st.session_state['path_nodes'] = path
            st.session_state['map_center'] = [(u[0]+v[0])/2, (u[1]+v[1])/2]
            
            if path:
                st.session_state['path_detail'] = get_turn_by_turn(G_map, path)
                
        except Exception as e: st.error(f"Lỗi: {e}")

    # HIỂN THỊ KẾT QUẢ
    if st.session_state['path_nodes']:
        path = st.session_state['path_nodes']
        details = st.session_state['path_detail']
        total_km = sum(d['dist'] for d in details) / 1000
        
        col_map, col_info = st.columns([2, 1])
        
        with col_info:
            st.markdown(f"### 📋 Lộ trình chi tiết")
            st.info(f"Tổng quãng đường: **{total_km:.2f} km**")
            with st.container(height=500):
                for i, step in enumerate(details):
                    st.markdown(f"""
                    <div class="route-step">
                        <div><span class="step-name">↪️ {step['name']}</span></div>
                        <span class="step-dist">{step['dist']:.0f} m</span>
                    </div>
                    """, unsafe_allow_html=True)

        with col_map:
            m = folium.Map(location=st.session_state['map_center'], zoom_start=14, tiles="OpenStreetMap")
            
            # 1. Vẽ Marker điểm chọn
            folium.Marker(locations[start_name], icon=folium.Icon(color="green", icon="play"), popup="Start").add_to(m)
            folium.Marker(locations[end_name], icon=folium.Icon(color="red", icon="flag"), popup="End").add_to(m)
            
            # 2. XỬ LÝ VẼ ĐƯỜNG CONG (GEOMETRY) - FIX LỖI CẮT NGANG
            route_coords = []
            # Thêm điểm đầu (nối từ Marker vào đường chính)
            start_node = G_map.nodes[path[0]]
            route_coords.append((start_node['y'], start_node['x']))
            
            for u, v in zip(path[:-1], path[1:]):
                # Lấy dữ liệu cạnh để xem nó cong hay thẳng
                edge = G_map.get_edge_data(u, v)[0]
                if 'geometry' in edge:
                    # Nếu đường cong -> Lấy toàn bộ các điểm uốn lượn
                    xs, ys = edge['geometry'].xy
                    route_coords.extend(list(zip(ys, xs)))
                else:
                    # Nếu đường thẳng -> Lấy điểm cuối
                    node_v = G_map.nodes[v]
                    route_coords.extend([(node_v['y'], node_v['x'])])

            # 3. Vẽ AntPath đè lên các điểm uốn lượn đó
            color = "orange" if "DFS" in algo_choice else ("purple" if "BFS" in algo_choice else "blue")
            AntPath(route_coords, color=color, weight=6, opacity=0.8, delay=1000).add_to(m)
            
            # 4. Vẽ đường nối từ Marker vào Tim đường (để ko bị hở)
            folium.PolyLine([locations[start_name], (G_map.nodes[path[0]]['y'], G_map.nodes[path[0]]['x'])], color="gray", weight=2, dash_array='5, 5').add_to(m)
            folium.PolyLine([locations[end_name], (G_map.nodes[path[-1]]['y'], G_map.nodes[path[-1]]['x'])], color="gray", weight=2, dash_array='5, 5').add_to(m)
            
            st_folium(m, width=800, height=600)
