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

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="Đồ Án Đồ Thị & Pleiku", layout="wide", page_icon="🗺️")
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; height: 3em; }
    h1 { color: #2E86C1; text-align: center; }
    .step-card { background-color: #F8F9F9; padding: 10px; border-radius: 5px; margin-bottom: 5px; border-left: 4px solid #2E86C1; }
    .step-dist { float: right; font-weight: bold; color: #E74C3C; }
    </style>
    """, unsafe_allow_html=True)

# Khởi tạo Session
if 'G' not in st.session_state: st.session_state['G'] = nx.Graph()
if 'path_nodes' not in st.session_state: st.session_state['path_nodes'] = []
if 'path_detail' not in st.session_state: st.session_state['path_detail'] = [] # Lưu chi tiết đường đi
if 'map_center' not in st.session_state: st.session_state['map_center'] = [13.9785, 108.0051]

# -----------------------------------------------------------------------------
# HÀM MỚI: TRÍCH XUẤT TÊN ĐƯỜNG VÀ ĐỘ DÀI
# -----------------------------------------------------------------------------
def get_turn_by_turn(G, path_nodes):
    if not path_nodes or len(path_nodes) < 2:
        return []

    route_segments = []
    current_name = None
    current_dist = 0
    
    # Duyệt qua từng cặp điểm trên đường đi
    for u, v in zip(path_nodes[:-1], path_nodes[1:]):
        # Lấy dữ liệu cạnh (edge)
        edge_data = G.get_edge_data(u, v)[0]
        
        # Lấy độ dài
        length = edge_data.get('length', 0)
        
        # Lấy tên đường (xử lý trường hợp tên là list hoặc string)
        name = edge_data.get('name', 'Đường chưa đặt tên')
        if isinstance(name, list):
            name = " / ".join(name) # Nếu có nhiều tên thì nối lại
            
        # Thuật toán gộp đường: Nếu vẫn đi trên đường cũ thì cộng dồn quãng đường
        if name == current_name:
            current_dist += length
        else:
            # Nếu đổi tên đường -> Lưu đoạn đường cũ lại
            if current_name is not None:
                route_segments.append({"name": current_name, "dist": current_dist})
            # Reset cho đường mới
            current_name = name
            current_dist = length
            
    # Lưu đoạn đường cuối cùng
    if current_name is not None:
        route_segments.append({"name": current_name, "dist": current_dist})
        
    return route_segments

# -----------------------------------------------------------------------------
# 2. HÀM VẼ LÝ THUYẾT (TAB 1)
# -----------------------------------------------------------------------------
def draw_graph_theory(graph, path_nodes=None, path_edges=None, title="Trực quan hóa"):
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
# 3. GIAO DIỆN CHÍNH
# -----------------------------------------------------------------------------
st.title("🕸️ ỨNG DỤNG TÌM ĐƯỜNG PLEIKU")
tab_theory, tab_map = st.tabs(["📚 PHẦN 1: LÝ THUYẾT", "🗺️ PHẦN 2: BẢN ĐỒ CHI TIẾT"])

# TAB 1: LÝ THUYẾT
with tab_theory:
    c1, c2 = st.columns([1, 2])
    with c1:
        type_opt = st.radio("Loại:", ["Vô hướng", "Có hướng"])
        inp = st.text_area("Cạnh:", value="A B 4\nA C 2\nB C 5\nB D 10\nC E 3\nD F 11\nE D 4", height=150)
        if st.button("🚀 Tạo Đồ Thị"):
            G = nx.DiGraph() if "Có" in type_opt else nx.Graph()
            for l in inp.strip().split('\n'):
                p = l.split()
                if len(p)>=2: G.add_edge(p[0], p[1], weight=int(p[2]) if len(p)>2 else 1)
            st.session_state['G'] = G; st.success("OK")
        st.download_button("💾 Lưu", inp, "graph.txt")
    with c2:
        if len(st.session_state['G'])>0: draw_graph_theory(st.session_state['G'])
    
    if len(st.session_state['G'])>0:
        st.divider(); col1, col2, col3 = st.columns(3)
        with col1:
            mode = st.selectbox("Xem:", ["Ma trận", "Danh sách"])
            if mode == "Ma trận": st.dataframe(pd.DataFrame(nx.adjacency_matrix(st.session_state['G']).todense(), index=st.session_state['G'].nodes(), columns=st.session_state['G'].nodes()), height=100)
            else: st.json(nx.to_dict_of_lists(st.session_state['G']))
            st.button("Check 2 Phía", on_click=lambda: st.write(f"Kết quả: {nx.is_bipartite(st.session_state['G'])}"))
        with col2:
            s = st.selectbox("Start", list(st.session_state['G'].nodes()))
            e = st.selectbox("End", list(st.session_state['G'].nodes()), index=len(st.session_state['G'])-1)
            if st.button("Dijkstra"):
                try: p=nx.shortest_path(st.session_state['G'],s,e,weight='weight'); draw_graph_theory(st.session_state['G'],path_nodes=p,title="Shortest")
                except: st.error("Không có đường")
            if st.button("BFS"): p=list(dict(nx.bfs_successors(st.session_state['G'],s)).keys()); p.insert(0,s); draw_graph_theory(st.session_state['G'],path_nodes=p,title="BFS")
        with col3:
            if st.button("Prim"):
                if not ("Có" in type_opt) and nx.is_connected(st.session_state['G']):
                    mst=nx.minimum_spanning_tree(st.session_state['G']); draw_graph_theory(st.session_state['G'],path_edges=list(mst.edges()),title="Prim MST")

# TAB 2: BẢN ĐỒ CHI TIẾT
with tab_map:
    st.header("🗺️ Dẫn đường chi tiết tại TP. Pleiku")
    
    @st.cache_resource
    def load_pleiku_map():
        # Lấy bán kính 3km
        return ox.graph_from_point((13.9785, 108.0051), dist=3000, network_type='drive')

    with st.spinner("Đang tải bản đồ Pleiku..."):
        try: G_map = load_pleiku_map(); st.success("✅ Đã tải xong!")
        except: st.error("Lỗi tải map"); st.stop()

    locs = {
        "Quảng trường Đại Đoàn Kết": (13.9785, 108.0051),
        "Sân vận động Pleiku": (13.9791, 108.0076),
        "Chợ Đêm Pleiku": (13.9745, 108.0068),
        "Vincom Plaza": (13.9804, 108.0053),
        "Coop Mart Pleiku": (13.9818, 108.0064),
        "Bệnh viện Đa khoa Tỉnh": (13.9822, 108.0019),
        "Công viên Diên Hồng": (13.9715, 108.0022),
        "Bưu điện Tỉnh": (13.9770, 108.0040),
        "KS Hoàng Anh Gia Lai": (13.9760, 108.0030),
        "Ngã 3 Hoa Lư": (13.9850, 108.0050)
    }

    c1, c2, c3 = st.columns([2, 2, 1.5])
    start = c1.selectbox("📍 Từ:", list(locs.keys()), index=0)
    end = c2.selectbox("🏁 Đến:", list(locs.keys()), index=5)
    algo = c3.selectbox("Thuật toán:", ["Dijkstra (Nhanh nhất)", "BFS (Ít rẽ nhất)", "DFS (Demo)"])
    
    if st.button("🚀 TÌM ĐƯỜNG CHI TIẾT", type="primary"):
        try:
            u, v = locs[start], locs[end]
            orig = ox.distance.nearest_nodes(G_map, u[1], u[0])
            dest = ox.distance.nearest_nodes(G_map, v[1], v[0])
            
            path = []
            if "Dijkstra" in algo: path = nx.shortest_path(G_map, orig, dest, weight='length')
            elif "BFS" in algo: path = nx.shortest_path(G_map, orig, dest, weight=None)
            elif "DFS" in algo: 
                try: path = next(nx.all_simple_paths(G_map, orig, dest, cutoff=80))
                except: path = []

            # Lưu dữ liệu
            st.session_state['path_nodes'] = path
            st.session_state['map_center'] = [(u[0]+v[0])/2, (u[1]+v[1])/2]
            
            # --- TÍNH TOÁN CHI TIẾT ---
            if path:
                details = get_turn_by_turn(G_map, path)
                st.session_state['path_detail'] = details # Lưu danh sách chỉ dẫn
                
        except Exception as e: st.error(f"Lỗi: {e}")

    # HIỂN THỊ CHI TIẾT ĐƯỜNG ĐI (BÊN TRÊN BẢN ĐỒ)
    if st.session_state['path_nodes']:
        path = st.session_state['path_nodes']
        details = st.session_state['path_detail']
        
        # Tính tổng km
        total_km = sum(d['dist'] for d in details) / 1000
        
        # Chia cột: Bên trái là bản đồ, Bên phải là chỉ dẫn
        col_map, col_text = st.columns([2, 1])
        
        with col_text:
            st.subheader("📋 Lộ trình chi tiết")
            st.info(f"Tổng quãng đường: **{total_km:.2f} km**")
            
            # Hiển thị danh sách cuộn
            with st.container(height=500):
                for i, step in enumerate(details):
                    st.markdown(f"""
                    <div class="step-card">
                        <b>{i+1}. {step['name']}</b>
                        <span class="step-dist">{step['dist']:.0f} m</span>
                    </div>
                    """, unsafe_allow_html=True)

        with col_map:
            m = folium.Map(location=st.session_state['map_center'], zoom_start=14, tiles="OpenStreetMap")
            folium.Marker(locs[start], icon=folium.Icon(color="green", icon="play"), popup="Start").add_to(m)
            folium.Marker(locs[end], icon=folium.Icon(color="red", icon="flag"), popup="End").add_to(m)
            
            # Vẽ AntPath (Kiến bò)
            route_coords = [(G_map.nodes[n]['y'], G_map.nodes[n]['x']) for n in path]
            AntPath(route_coords, color="blue", weight=6, opacity=0.8, delay=1000).add_to(m)
            
            st_folium(m, width=800, height=500)
