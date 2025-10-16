import streamlit as st
import os
import base64
from PIL import Image
import io
from pathlib import Path
import uuid

def create_upload_directory():
    """创建上传目录"""
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)
    
    # 创建子目录
    (upload_dir / "images").mkdir(exist_ok=True)
    (upload_dir / "videos").mkdir(exist_ok=True)
    
    return upload_dir

def save_uploaded_file(uploaded_file, file_type="image"):
    """保存上传的文件"""
    upload_dir = create_upload_directory()
    
    if file_type == "image":
        save_path = upload_dir / "images" / uploaded_file.name
    else:
        save_path = upload_dir / "videos" / uploaded_file.name
    
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return str(save_path)

def drag_drop_image_uploader(key, label="上传图片", help_text="支持拖拽上传图片文件"):
    """
    拖拽式图片上传组件
    
    Args:
        key: 组件的唯一标识符
        label: 显示标签
        help_text: 帮助文本
    
    Returns:
        tuple: (uploaded_file, file_path)
    """
    st.markdown(f"### {label}")
    
    # 自定义CSS样式
    st.markdown("""
    <style>
    .upload-container {
        border: 2px dashed #1f77b4;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        background-color: #f8f9fa;
        margin: 10px 0;
        transition: all 0.3s ease;
    }
    
    .upload-container:hover {
        border-color: #0d5aa7;
        background-color: #e6f3ff;
    }
    
    .upload-icon {
        font-size: 48px;
        color: #1f77b4;
        margin-bottom: 10px;
    }
    
    .upload-text {
        color: #666;
        font-size: 16px;
        margin-bottom: 10px;
    }
    
    .upload-help {
        color: #999;
        font-size: 14px;
    }
    
    .image-preview {
        max-width: 300px;
        max-height: 200px;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 上传区域
    st.markdown(f"""
    <div class="upload-container">
        <div class="upload-icon">📷</div>
        <div class="upload-text">拖拽图片到此处或点击选择文件</div>
        <div class="upload-help">{help_text}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # 文件上传器
    uploaded_file = st.file_uploader(
        "选择图片文件",
        type=['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'],
        key=f"image_uploader_{key}",
        label_visibility="collapsed"
    )
    
    file_path = None
    
    if uploaded_file is not None:
        # 显示图片预览
        try:
            image = Image.open(uploaded_file)
            st.markdown("#### 📷 图片预览")
            
            # 使用增强的图片预览
            enhanced_image_preview(image, uploaded_file.name, f"upload_{key}")
            
            # 保存文件
            file_path = save_uploaded_file(uploaded_file, "image")
            st.success(f"✅ 图片已保存: {file_path}")
            
        except Exception as e:
            st.error(f"❌ 图片处理失败: {str(e)}")
    
    return uploaded_file, file_path

def drag_drop_video_uploader(key, label="上传视频", help_text="支持拖拽上传视频文件"):
    """
    拖拽式视频上传组件
    
    Args:
        key: 组件的唯一标识符
        label: 显示标签
        help_text: 帮助文本
    
    Returns:
        tuple: (uploaded_file, file_path)
    """
    st.markdown(f"### {label}")
    
    # 上传区域
    st.markdown(f"""
    <div class="upload-container">
        <div class="upload-icon">🎥</div>
        <div class="upload-text">拖拽视频到此处或点击选择文件</div>
        <div class="upload-help">{help_text}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # 文件上传器
    uploaded_file = st.file_uploader(
        "选择视频文件",
        type=['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv'],
        key=f"video_uploader_{key}",
        label_visibility="collapsed"
    )
    
    file_path = None
    
    if uploaded_file is not None:
        # 显示视频信息
        st.markdown("#### 🎥 视频信息")
        st.write(f"**文件名:** {uploaded_file.name}")
        st.write(f"**文件大小:** {uploaded_file.size / (1024*1024):.2f} MB")
        
        # 保存文件
        try:
            file_path = save_uploaded_file(uploaded_file, "video")
            st.success(f"✅ 视频已保存: {file_path}")
            
            # 显示视频预览（如果文件不太大）
            if uploaded_file.size < 50 * 1024 * 1024:  # 50MB以下显示预览
                st.video(uploaded_file)
            else:
                st.info("📹 视频文件较大，已保存但不显示预览")
                
        except Exception as e:
            st.error(f"❌ 视频处理失败: {str(e)}")
    
    return uploaded_file, file_path

def drag_drop_media_uploader(key, label="上传媒体文件", help_text="支持拖拽上传图片和视频文件"):
    """
    拖拽式媒体文件上传组件（支持图片和视频）
    
    Args:
        key: 组件的唯一标识符
        label: 显示标签
        help_text: 帮助文本
    
    Returns:
        dict: {"image": (file, path), "video": (file, path)}
    """
    st.markdown(f"### {label}")
    
    col1, col2 = st.columns(2)
    
    result = {"image": (None, None), "video": (None, None)}
    
    with col1:
        image_file, image_path = drag_drop_image_uploader(f"{key}_image", "📷 图片上传", "支持 PNG, JPG, JPEG, GIF 等格式")
        result["image"] = (image_file, image_path)
    
    with col2:
        video_file, video_path = drag_drop_video_uploader(f"{key}_video", "🎥 视频上传", "支持 MP4, AVI, MOV 等格式")
        result["video"] = (video_file, video_path)
    
    return result

def enhanced_image_preview(image, image_name, key_suffix=""):
    """
    增强的图片预览组件，支持缩放、全屏、旋转等功能
    
    Args:
        image: PIL Image对象
        image_name: 图片名称
        key_suffix: 组件key后缀
    """
    unique_key = f"img_preview_{key_suffix}_{uuid.uuid4().hex[:8]}"
    
    # 获取图片信息
    width, height = image.size
    file_size = len(image.tobytes()) / 1024  # KB
    
    # 图片信息显示
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown(f"**📷 {image_name}**")
    with col2:
        st.markdown(f"**尺寸:** {width}×{height}")
    with col3:
        st.markdown(f"**大小:** {file_size:.1f}KB")
    
    # 控制按钮
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        zoom_in = st.button("🔍 放大", key=f"zoom_in_{unique_key}")
    with col2:
        zoom_out = st.button("🔍 缩小", key=f"zoom_out_{unique_key}")
    with col3:
        rotate_left = st.button("↺ 左转", key=f"rotate_left_{unique_key}")
    with col4:
        rotate_right = st.button("↻ 右转", key=f"rotate_right_{unique_key}")
    with col5:
        fullscreen = st.button("⛶ 全屏", key=f"fullscreen_{unique_key}")
    
    # 初始化session state
    if f"zoom_{unique_key}" not in st.session_state:
        st.session_state[f"zoom_{unique_key}"] = 1.0
    if f"rotation_{unique_key}" not in st.session_state:
        st.session_state[f"rotation_{unique_key}"] = 0
    
    # 处理按钮点击
    if zoom_in:
        st.session_state[f"zoom_{unique_key}"] = min(3.0, st.session_state[f"zoom_{unique_key}"] + 0.2)
    if zoom_out:
        st.session_state[f"zoom_{unique_key}"] = max(0.5, st.session_state[f"zoom_{unique_key}"] - 0.2)
    if rotate_left:
        st.session_state[f"rotation_{unique_key}"] = (st.session_state[f"rotation_{unique_key}"] - 90) % 360
    if rotate_right:
        st.session_state[f"rotation_{unique_key}"] = (st.session_state[f"rotation_{unique_key}"] + 90) % 360
    
    # 应用变换
    display_image = image.copy()
    if st.session_state[f"rotation_{unique_key}"] != 0:
        display_image = display_image.rotate(st.session_state[f"rotation_{unique_key}"], expand=True)
    
    # 计算显示尺寸
    zoom = st.session_state[f"zoom_{unique_key}"]
    display_width = int(min(600, width * zoom))
    
    # 显示图片
    if fullscreen:
        # 全屏模式
        st.markdown("### 🖼️ 全屏预览")
        st.image(display_image, caption=f"{image_name} (缩放: {zoom:.1f}x, 旋转: {st.session_state[f'rotation_{unique_key}']}°)", 
                use_column_width=True)
        if st.button("❌ 关闭全屏", key=f"close_fullscreen_{unique_key}"):
            st.rerun()
    else:
        # 普通预览模式
        st.image(display_image, caption=f"{image_name} (缩放: {zoom:.1f}x)", width=display_width)
    
    # 显示当前状态
    st.markdown(f"**当前状态:** 缩放 {zoom:.1f}x | 旋转 {st.session_state[f'rotation_{unique_key}']}°")

def display_uploaded_media(image_path=None, video_path=None):
    """
    显示已上传的媒体文件
    
    Args:
        image_path: 图片路径
        video_path: 视频路径
    """
    if image_path or video_path:
        st.markdown("#### 📁 已上传的媒体文件")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if image_path and os.path.exists(image_path):
                st.markdown("**📷 图片:**")
                try:
                    image = Image.open(image_path)
                    # 使用增强的图片预览
                    enhanced_image_preview(image, os.path.basename(image_path), f"uploaded_{hash(image_path)}")
                except Exception as e:
                    st.error(f"无法显示图片: {str(e)}")
            else:
                st.info("暂无图片")
        
        with col2:
            if video_path and os.path.exists(video_path):
                st.markdown("**🎥 视频:**")
                try:
                    st.video(video_path)
                    # 显示视频信息
                    file_size = os.path.getsize(video_path) / (1024 * 1024)  # MB
                    st.markdown(f"**文件大小:** {file_size:.1f}MB")
                except Exception as e:
                    st.error(f"无法显示视频: {str(e)}")
            else:
                st.info("暂无视频")