import streamlit as st
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
import osmnx as ox
import folium
from folium.plugins import AntPath
from streamlit_folium import st_folium
import warnings

# Tắt các cảnh báo không cần thiết
warnings.filterwarnings("ignore")

# -----------------------------------------------------------------------------
# 1. CẤU HÌNH GIAO DIỆN
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Đồ Án Đồ Thị & Pleiku Map", layout="wide", page_icon="🗺️")

# CSS tùy chỉnh cho giao diện đẹp
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; height: 3em; }
    h1 { color: #2E86C1; text-align: center; font-family: 'Segoe UI', sans-serif; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #f0f2f6; border-radius: 5px; }
    .stTabs [aria-selected="true"] { background-color: #D6EAF8; font-weight: bold; color: #2874A6; }
    
    /* Style cho thẻ lộ trình */
    .route-card {
        background-color: white;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        margin-bottom: 10px;
        border-left: 5px solid #3498DB;
    }
    .step-text { font-size: 16px; color: #34495E; font-weight: 500; }
    .dist-badge { 
        float: right; 
        background-color: #FDEDEC; 
        color: #C0392B; 
        padding: 2px 8px; 
        border-radius: 12px; 
        font-size: 14px; 
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# Khởi tạo Session State (Bộ nhớ tạm)
if 'G' not in st.session_state: st.session_state['G'] = nx.Graph()
if 'graph_type' not in st.session_state: st.session_state['graph_type'] = "Vô hướng"
if 'path_nodes' not in st.session_state: st.session_state['path_nodes'] = []
if 'path_detail' not in st.session_state: st.session_state['path_detail'] = []
if 'map_center' not in st.session_state: st.session_state['map_center'] = [13.9785, 108.0051]

# -----------------------------------------------------------------------------
# HÀM XỬ LÝ: LẤY THÔNG TIN LỘ TRÌNH CHI TIẾT
# -----------------------------------------------------------------------------
def get_route_details(G, path_nodes):
    if not path_nodes or len(path_nodes) < 2: return []
    
    steps = []
    current_name = None
    current_dist = 0
    
    for u, v in zip(path_nodes[:-1], path_nodes[1:]):
        data = G.get_edge_data(u, v)[0]
        length = data.get('length', 0)
        name = data.get('name', 'Đường chưa đặt tên')
        
        # Xử lý tên đường (có thể là list)
        if isinstance(name, list): name = " / ".join(name)
        
        # Gộp các đoạn đường cùng tên
        if name == current_name:
            current_dist += length
        else:
            if current_name:
                steps.append({"name": current_name, "dist": current_dist})
            current_name = name
            current_dist = length
            
    # Thêm đoạn cuối
    if current_name:
        steps.append({"name": current_name, "dist": current_dist})
        
    return steps

# -----------------------------------------------------------------------------
# HÀM VẼ: ĐỒ THỊ LÝ THUYẾT (TAB 1)
# -----------------------------------------------------------------------------
def draw_theory_graph(graph, path=None, edges=None, title="Đồ thị"):
    fig, ax = plt.subplots(figsize=(10, 6))
    pos = nx.spring_layout(graph, seed=42)
    
    # Vẽ nền
    nx.draw_networkx_nodes(graph, pos, node_size=700, node_color="#AED6F1", ax=ax)
    nx.draw_networkx_edges(graph, pos, width=2, alpha=0.5, edge_color="gray", ax=ax)
    nx.draw_networkx_labels(graph, pos, font_size=12, font_weight="bold", ax=ax)
    edge_labels = nx.get_edge_attributes(graph, 'weight')
    nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels, font_size=10, ax=ax)
    
    # Highlight (Đường đi)
    if path:
        nx.draw_networkx_nodes(graph, pos, nodelist=path, node_color="#E74C3C", node_size=800, ax=ax)
        if len(path) > 1:
            path_edges = list(zip(path, path[1:]))
            nx.draw_networkx_edges(graph, pos, edgelist=path_edges, width=4, edge_color="#E74C3C", ax=ax)
            
    # Highlight (Cạnh - dùng cho Prim)
    if edges:
        nx.draw_networkx_edges(graph, pos, edgelist=edges, width=4, edge_color="#27AE60", ax=ax)
        
    ax.set_title(title, fontsize=14, color="#2874A6")
    ax.axis('off')
    st.pyplot(fig)

# -----------------------------------------------------------------------------
# GIAO DIỆN CHÍNH
# -----------------------------------------------------------------------------
st.title("ỨNG DỤNG MÔ PHỎNG THUẬT TOÁN ĐỒ THỊ")

# TẠO 2 TAB CHÍNH
tab1, tab2 = st.tabs(["📚 PHẦN 1: LÝ THUYẾT (FULL YÊU CẦU)", "🗺️ PHẦN 2: BẢN ĐỒ PLEIKU (50 ĐỊA ĐIỂM)"])

# =============================================================================
# TAB 1: LÝ THUYẾT (GIẢI QUYẾT 7 YÊU CẦU CỦA GIÁO VIÊN)
# =============================================================================
with tab1:
    col_input, col_viz = st.columns([1, 2])
    
    with col_input:
        st.subheader("1. Nhập liệu")
        # YC 6: Loại đồ thị
        type_opt = st.radio("Loại:", ["Vô hướng", "Có hướng"])
        is_directed = "Có hướng" in type_opt
        
        # YC 6: Nhập cạnh
        inp = st.text_area("Danh sách cạnh (u v w):", value="A B 4\nA C 2\nB C 5\nB D 10\nC E 3\nD F 11\nE D 4", height=150)
        
        # YC 1: Tạo đồ thị
        if st.button("🚀 Tạo Đồ Thị (YC1)"):
            try:
                G = nx.DiGraph() if is_directed else nx.Graph()
                for line in inp.strip().split('\n'):
                    p = line.split()
                    if len(p) >= 2:
                        w = int(p[2]) if len(p) > 2 else 1
                        G.add_edge(p[0], p[1], weight=w)
                st.session_state['G'] = G
                st.session_state['graph_type'] = type_opt
                st.success("Đã tạo xong!")
            except:
                st.error("Lỗi dữ liệu nhập!")
        
        # YC 2: Lưu file
        st.download_button("💾 Lưu đồ thị (.txt)", inp, "graph_data.txt")

    with col_viz:
        G = st.session_state['G']
        if len(G) > 0:
            draw_theory_graph(G, title=f"Mô hình ({st.session_state['graph_type']})")
        else:
            st.info("👈 Vui lòng nhập dữ liệu để bắt đầu.")

    if len(G) > 0:
        st.divider()
        c1, c2, c3 = st.columns(3)
        
        # YC 5 & 6: Biểu diễn & Tính chất
        with c1:
            st.markdown("##### 🛠️ Biểu diễn")
            mode = st.selectbox("Dạng xem:", ["Ma trận kề", "Danh sách kề"])
            if mode == "Ma trận kề":
                st.dataframe(pd.DataFrame(nx.adjacency_matrix(G).todense(), index=G.nodes(), columns=G.nodes()), height=150)
            else:
                st.json(nx.to_dict_of_lists(G), expanded=False)
            
            if st.button("Kiểm tra 2 phía (YC5)"):
                res = "✅ Có" if nx.is_bipartite(G) else "❌ Không"
                st.write(f"Kết quả: {res}")

        # YC 3 & 4: Thuật toán tìm đường
        with c2:
            st.markdown("##### 🔍 Duyệt & Tìm đường")
            s = st.selectbox("Start:", list(G.nodes()))
            e = st.selectbox("End:", list(G.nodes()), index=len(G.nodes())-1)
            
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if st.button("BFS (YC4)"):
                    path = list(dict(nx.bfs_successors(G, s)).keys()); path.insert(0, s)
                    st.success(f"BFS: {path}"); draw_theory_graph(G, path=path, title="BFS")
            with col_b2:
                if st.button("DFS (YC4)"):
                    path = list(nx.dfs_preorder_nodes(G, s))
                    st.success(f"DFS: {path}"); draw_theory_graph(G, path=path, title="DFS")
            
            if st.button("Dijkstra (Shortest)"):
                try:
                    p = nx.shortest_path(G, s, e, weight='weight')
                    draw_theory_graph(G, path=p, title="Đường đi ngắn nhất")
                except: st.error("Không có đường đi")

        # YC 7: Nâng cao (Prim)
        with c3:
            st.markdown("##### 🌲 Nâng cao")
            if st.button("Prim (MST) (YC7)"):
                if not is_directed and nx.is_connected(G):
                    mst = nx.minimum_spanning_tree(G, algorithm='prim')
                    st.info(f"Tổng trọng số: {mst.size(weight='weight')}")
                    draw_theory_graph(G, edges=list(mst.edges()), title="Cây khung Prim")
                else:
                    st.warning("Prim chỉ chạy trên đồ thị vô hướng liên thông.")

# =============================================================================
# TAB 2: BẢN ĐỒ PLEIKU (50 ĐỊA ĐIỂM - CHÍNH XÁC CAO)
# =============================================================================
with tab2:
    st.header("🗺️ Tìm đường chi tiết tại TP. Pleiku")

    # 1. LOAD MAP: Lấy bán kính 5km để bao trùm cả Sân bay và Biển Hồ
    @st.cache_resource
    def load_pleiku_map():
        # Quảng trường Đại Đoàn Kết (Tâm)
        point = (13.9785, 108.0051)
        return ox.graph_from_point(point, dist=5000, network_type='drive')

    with st.spinner("Đang tải dữ liệu bản đồ Pleiku (Vui lòng đợi)..."):
        try:
            G_map = load_pleiku_map()
            st.success("✅ Đã tải xong hệ thống giao thông!")
        except:
            st.error("Lỗi kết nối bản đồ. Vui lòng thử lại."); st.stop()

    # 2. DANH SÁCH 50 ĐỊA ĐIỂM (TỌA ĐỘ CHUẨN)
    locations = {
        "Quảng trường Đại Đoàn Kết": (13.9785, 108.0051),
        "Sân bay Pleiku": (14.0044, 108.0172),
        "Biển Hồ (Tơ Nưng)": (14.0534, 108.0035),
        "Bến xe Đức Long": (13.9556, 108.0264),
        "Sân vận động Pleiku": (13.9791, 108.0076),
        "Chợ Đêm Pleiku": (13.9745, 108.0068),
        "Chợ Trung tâm Pleiku": (13.9750, 108.0080),
        "Chợ Thống Nhất": (13.9800, 108.0150),
        "Chợ Phù Đổng": (13.9700, 108.0100),
        "Chợ Hoa Lư": (13.9850, 108.0050),
        "TTTM Vincom Plaza": (13.9804, 108.0053),
        "Coop Mart Pleiku": (13.9818, 108.0064),
        "Bệnh viện Đa khoa Tỉnh": (13.9822, 108.0019),
        "Bệnh viện ĐH Y Dược HAGL": (13.9700, 108.0000),
        "Bệnh viện Nhi Gia Lai": (13.9600, 108.0100),
        "Bệnh viện Mắt Cao Nguyên": (13.9650, 108.0150),
        "Bệnh viện 331": (13.9900, 108.0200),
        "Bệnh viện TP Pleiku": (13.9780, 108.0150),
        "Công viên Diên Hồng": (13.9715, 108.0022),
        "Công viên Đồng Xanh": (13.9800, 108.0500),
        "Chùa Minh Thành": (13.9680, 108.0100),
        "Chùa Bửu Minh": (14.0200, 108.0100),
        "Nhà thờ Đức An": (13.9750, 108.0050),
        "Nhà thờ Thăng Thiên": (13.9850, 108.0050),
        "Nhà thờ Plei Chuet": (13.9700, 108.0300),
        "Bưu điện Tỉnh Gia Lai": (13.9770, 108.0040),
        "Trường THPT Chuyên Hùng Vương": (13.9850, 108.0100),
        "Trường THPT Pleiku": (13.9800, 108.0120),
        "Trường THPT Phan Bội Châu": (13.9750, 108.0200),
        "Trường THPT Lê Lợi": (13.9700, 108.0150),
        "Trường CĐ Sư phạm Gia Lai": (13.9600, 108.0200),
        "Phân hiệu ĐH Nông Lâm": (13.9550, 108.0300),
        "Khách sạn Hoàng Anh Gia Lai": (13.9760, 108.0030),
        "Khách sạn Tre Xanh": (13.9790, 108.0060),
        "Khách sạn Khánh Linh": (13.9780, 108.0050),
        "Khách sạn Mê Kông": (13.9750, 108.0020),
        "Khách sạn Boston": (13.9720, 108.0050),
        "Công an Tỉnh Gia Lai": (13.9780, 108.0020),
        "Ủy ban Nhân dân Tỉnh": (13.9790, 108.0040),
        "Sở Giáo dục & Đào tạo": (13.9775, 108.0045),
        "Bảo tàng Tỉnh Gia Lai": (13.9780, 108.0055),
        "Ngã 3 Hoa Lư": (13.9850, 108.0050),
        "Ngã 4 Biển Hồ": (14.0000, 108.0000),
        "Ngã 3 Phù Đổng": (13.9700, 108.0050),
        "Ngã 3 Diệp Kính": (13.9750, 108.0070),
        "Rạp Touch Cinema": (13.9700, 108.0100),
        "Hồ Đức An": (13.9740, 108.0040),
        "Làng Văn hóa Plei Ốp": (13.9820, 108.0080),
        "Núi Hàm Rồng": (13.8900, 108.0500),
        "Học viện Bóng đá HAGL": (13.9500, 108.0500)
    }

    # 3. ĐIỀU KHIỂN
    c_start, c_end, c_algo = st.columns([2, 2, 1.5])
    start_name = c_start.selectbox("📍 Điểm Xuất Phát:", sorted(locations.keys()), index=0)
    end_name = c_end.selectbox("🏁 Điểm Đến:", sorted(locations.keys()), index=1)
    algo_choice = c_algo.selectbox("Thuật toán:", ["Dijkstra (Nhanh nhất)", "BFS (Ít rẽ nhất)", "DFS (Demo)"])
    
    if st.button("🚀 TÌM ĐƯỜNG CHI TIẾT", type="primary"):
        try:
            # Lấy tọa độ
            u_coord, v_coord = locations[start_name], locations[end_name]
            
            # Tìm node gần nhất trên đồ thị
            orig = ox.distance.nearest_nodes(G_map, u_coord[1], u_coord[0])
            dest = ox.distance.nearest_nodes(G_map, v_coord[1], v_coord[0])
            
            path = []
            if "Dijkstra" in algo_choice:
                path = nx.shortest_path(G_map, orig, dest, weight='length')
            elif "BFS" in algo_choice:
                path = nx.shortest_path(G_map, orig, dest, weight=None)
            elif "DFS" in algo_choice:
                try: path = next(nx.all_simple_paths(G_map, orig, dest, cutoff=100))
                except: path = []

            # Lưu vào Session
            st.session_state['path_nodes'] = path
            st.session_state['map_center'] = [(u_coord[0]+v_coord[0])/2, (u_coord[1]+v_coord[1])/2]
            
            # Tính toán chi tiết
            if path:
                st.session_state['path_detail'] = get_route_details(G_map, path)
            else:
                st.error("Không tìm thấy đường đi giữa 2 điểm này!")
                
        except Exception as e:
            st.error(f"Lỗi: {e}")

    # 4. HIỂN THỊ KẾT QUẢ (CHIA 2 CỘT)
    if st.session_state['path_nodes']:
        path = st.session_state['path_nodes']
        details = st.session_state['path_detail']
        total_km = sum(d['dist'] for d in details) / 1000
        
        col_map, col_text = st.columns([2, 1])
        
        with col_text:
            st.markdown("### 📋 Lộ trình chi tiết")
            st.success(f"Tổng quãng đường: **{total_km:.2f} km**")
            
            with st.container(height=600): # Thanh cuộn
                for i, step in enumerate(details):
                    st.markdown(f"""
                    <div class="route-card">
                        <div class="step-text">
                            {i+1}. {step['name']}
                            <span class="dist-badge">{step['dist']:.0f} m</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        with col_map:
            # Tạo bản đồ
            m = folium.Map(location=st.session_state['map_center'], zoom_start=14, tiles="OpenStreetMap")
            
            # Marker điểm chọn
            folium.Marker(locations[start_name], icon=folium.Icon(color="green", icon="play"), popup=start_name).add_to(m)
            folium.Marker(locations[end_name], icon=folium.Icon(color="red", icon="flag"), popup=end_name).add_to(m)
            
            # --- QUAN TRỌNG: VẼ ĐƯỜNG CONG MỀM MẠI (DÙNG GEOMETRY) ---
            route_coords = []
            
            # Điểm đầu
            start_node = G_map.nodes[path[0]]
            route_coords.append((start_node['y'], start_node['x']))
            
            for u, v in zip(path[:-1], path[1:]):
                edge = G_map.get_edge_data(u, v)[0]
                if 'geometry' in edge:
                    # Nếu có geometry (đường cong), lấy toàn bộ điểm uốn
                    xs, ys = edge['geometry'].xy
                    # zip(ys, xs) vì Folium dùng (Lat, Lon)
                    route_coords.extend(list(zip(ys, xs)))
                else:
                    # Nếu đường thẳng
                    node_v = G_map.nodes[v]
                    route_coords.extend([(node_v['y'], node_v['x'])])
            
            # Vẽ AntPath (Hiệu ứng kiến bò)
            color = "orange" if "DFS" in algo_choice else ("purple" if "BFS" in algo_choice else "blue")
            AntPath(route_coords, color=color, weight=6, opacity=0.8, delay=1000).add_to(m)
            
            # Vẽ đường nét đứt nối Marker vào tim đường
            folium.PolyLine([locations[start_name], route_coords[0]], color="gray", weight=2, dash_array='5, 5').add_to(m)
            folium.PolyLine([locations[end_name], route_coords[-1]], color="gray", weight=2, dash_array='5, 5').add_to(m)
            
            st_folium(m, width=900, height=600)
