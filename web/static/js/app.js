// Telegram 表情包制作器 - 前端JavaScript

class StickerMaker {
    constructor() {
        this.uploadedFiles = [];
        this.currentTask = null;
        this.config = {};
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.loadConfig();
        this.setupTabs();
        this.setupFileUpload();
    }
    
    // 事件监听器设置
    setupEventListeners() {
        // 配置相关
        document.getElementById('config-form').addEventListener('submit', (e) => this.saveConfig(e));
        document.getElementById('test-config').addEventListener('click', () => this.testConfig());
        document.getElementById('refresh-config').addEventListener('click', () => this.loadConfig());
        
        // 代理设置相关
        document.getElementById('proxy-enabled').addEventListener('change', (e) => this.toggleProxySettings(e));
        document.getElementById('proxy-auth-enabled').addEventListener('change', (e) => this.toggleProxyAuth(e));
        
        // 文件上传相关
        document.getElementById('file-input').addEventListener('change', (e) => this.handleFileSelect(e));
        document.getElementById('sticker-form').addEventListener('submit', (e) => this.createStickerPack(e));
        document.getElementById('select-files-btn').addEventListener('click', () => {
            document.getElementById('file-input').click();
        });
        
        // 表情包管理相关
        document.getElementById('search-pack-btn').addEventListener('click', () => this.searchStickerPack());
        document.getElementById('pack-search').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.searchStickerPack();
        });
        
        // 模态框相关
        document.getElementById('save-sticker-edit').addEventListener('click', () => this.saveStickerEdit());
        
        // 移动端触摸优化 - 事件委托
        this.setupMobileEventDelegation();
    }
    
    // 移动端事件委托设置 - 新增方法
    setupMobileEventDelegation() {
        // 使用事件委托处理动态生成的按钮
        document.body.addEventListener('click', (e) => {
            const target = e.target.closest('button, .btn, .nav-link');
            if (!target) return;
            
            // 添加触摸反馈
            this.addTouchFeedback(target);
            
            // 处理特定按钮点击
            this.handleButtonClick(e, target);
        });
        
        // 触摸事件委托
        document.body.addEventListener('touchstart', (e) => {
            const target = e.target.closest('button, .btn, .nav-link');
            if (target) {
                this.addTouchFeedback(target);
            }
        }, { passive: true });
        
        // 防止双击缩放 - 移动端优化
        let lastTouchEnd = 0;
        document.addEventListener('touchend', (e) => {
            const now = Date.now();
            if (now - lastTouchEnd <= 300) {
                e.preventDefault();
            }
            lastTouchEnd = now;
        }, { passive: false });
    }
    
    // 触摸反馈 - 新增方法
    addTouchFeedback(element) {
        element.style.transform = 'scale(0.98)';
        element.style.opacity = '0.8';
        
        setTimeout(() => {
            element.style.transform = '';
            element.style.opacity = '';
        }, 150);
    }
    
    // 统一按钮点击处理 - 新增方法
    handleButtonClick(e, target) {
        // 防止重复点击
        if (target.disabled || target.classList.contains('processing')) {
            e.preventDefault();
            return;
        }
        
        // 添加处理状态
        target.classList.add('processing');
        setTimeout(() => {
            target.classList.remove('processing');
        }, 1000);
    }
    
    // 标签页设置
    setupTabs() {
        document.querySelectorAll('[data-tab]').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const tab = e.target.closest('[data-tab]').dataset.tab;
                this.switchTab(tab);
            });
        });
    }
    
    switchTab(tabName) {
        // 更新导航
        document.querySelectorAll('[data-tab]').forEach(link => {
            link.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        
        // 更新内容
        document.querySelectorAll('.tab-pane').forEach(pane => {
            pane.classList.remove('active');
        });
        document.getElementById(tabName).classList.add('active');
    }
    
    // 文件上传设置
    setupFileUpload() {
        const uploadZone = document.getElementById('upload-zone');
        const fileInput = document.getElementById('file-input');
        
        // 拖拽功能
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadZone.addEventListener(eventName, this.preventDefaults, false);
        });
        
        ['dragenter', 'dragover'].forEach(eventName => {
            uploadZone.addEventListener(eventName, () => {
                uploadZone.classList.add('dragover');
            }, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            uploadZone.addEventListener(eventName, () => {
                uploadZone.classList.remove('dragover');
            }, false);
        });
        
        uploadZone.addEventListener('drop', (e) => this.handleDrop(e), false);
        
        // 添加触摸支持 - 移动端优化
        this.setupTouchEvents(uploadZone, fileInput);
        
        // 点击事件 - 使用事件委托优化
        uploadZone.addEventListener('click', (e) => {
            e.preventDefault();
            fileInput.click();
        });
        
        // 键盘支持
        uploadZone.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                fileInput.click();
            }
        });
    }
    
    // 触摸事件设置 - 新增方法
    setupTouchEvents(uploadZone, fileInput) {
        let touchStartTime = 0;
        
        // 触摸开始
        uploadZone.addEventListener('touchstart', (e) => {
            touchStartTime = Date.now();
            uploadZone.classList.add('dragover');
        }, { passive: true });
        
        // 触摸结束
        uploadZone.addEventListener('touchend', (e) => {
            const touchDuration = Date.now() - touchStartTime;
            uploadZone.classList.remove('dragover');
            
            // 如果是短触摸（小于500ms），触发文件选择
            if (touchDuration < 500) {
                e.preventDefault();
                fileInput.click();
            }
        }, { passive: false });
        
        // 触摸取消
        uploadZone.addEventListener('touchcancel', () => {
            uploadZone.classList.remove('dragover');
        }, { passive: true });
    }
    
    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    handleDrop(e) {
        const files = e.dataTransfer.files;
        this.handleFiles(files);
    }
    
    handleFileSelect(e) {
        this.handleFiles(e.target.files);
    }
    
    handleFiles(files) {
        const fileArray = Array.from(files);
        const validFiles = fileArray.filter(file => this.validateFile(file));
        
        if (validFiles.length > 0) {
            this.uploadFiles(validFiles);
        }
    }
    
    validateFile(file) {
        const allowedTypes = ['image/png', 'image/jpeg', 'image/gif', 'image/webp', 'video/mp4', 'video/webm'];
        const maxSize = 50 * 1024 * 1024; // 50MB
        
        if (!allowedTypes.includes(file.type)) {
            this.showAlert(`不支持的文件类型: ${file.name}`, 'warning');
            return false;
        }
        
        if (file.size > maxSize) {
            this.showAlert(`文件过大: ${file.name} (超过50MB)`, 'warning');
            return false;
        }
        
        return true;
    }
    
    async uploadFiles(files) {
        const formData = new FormData();
        files.forEach(file => formData.append('files', file));
        
        try {
            this.showLoading(true);
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.uploadedFiles = result.files;
                this.displayUploadedFiles();
                this.updateCreateButton();
                
                if (result.errors.length > 0) {
                    result.errors.forEach(error => this.showAlert(error, 'warning'));
                }
            } else {
                this.showAlert(result.error, 'danger');
            }
        } catch (error) {
            this.showAlert('上传失败: ' + error.message, 'danger');
        } finally {
            this.showLoading(false);
        }
    }
    
    displayUploadedFiles() {
        const fileList = document.getElementById('file-list');
        const fileItems = document.getElementById('file-items');
        
        if (this.uploadedFiles.length === 0) {
            fileList.style.display = 'none';
            return;
        }
        
        fileList.style.display = 'block';
        fileItems.innerHTML = '';
        
        this.uploadedFiles.forEach((file, index) => {
            const item = document.createElement('div');
            item.className = 'file-item d-flex align-items-center';
            item.innerHTML = `
                <div class="me-3">
                    ${this.getFilePreview(file)}
                </div>
                <div class="flex-grow-1">
                    <h6 class="mb-1">${file.filename}</h6>
                    <small class="text-muted">
                        ${this.formatFileSize(file.size)} • ${file.type}
                    </small>
                </div>
                <div>
                    <button class="btn btn-sm btn-outline-danger remove-file-btn" data-file-index="${index}">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            `;
            fileItems.appendChild(item);
        });
        
        // 使用事件委托处理删除按钮
        this.setupFileItemEvents();
    }
    
    // 文件项事件设置 - 新增方法
    setupFileItemEvents() {
        const fileItems = document.getElementById('file-items');
        
        // 移除旧的事件监听器
        fileItems.removeEventListener('click', this.handleFileItemClick);
        
        // 添加新的事件监听器
        this.handleFileItemClick = (e) => {
            const removeBtn = e.target.closest('.remove-file-btn');
            if (removeBtn) {
                e.preventDefault();
                const index = parseInt(removeBtn.dataset.fileIndex);
                this.removeFile(index);
            }
        };
        
        fileItems.addEventListener('click', this.handleFileItemClick);
    }
    
    getFilePreview(file) {
        if (file.type.startsWith('.mp4') || file.type.startsWith('.webm')) {
            return '<i class="bi bi-play-circle file-preview d-flex align-items-center justify-content-center bg-light" style="font-size: 24px;"></i>';
        } else if (file.type.startsWith('.gif')) {
            return `<img src="/uploads/${file.unique_filename}" class="file-preview" alt="预览">`;
        } else {
            return `<img src="/uploads/${file.unique_filename}" class="file-preview" alt="预览">`;
        }
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    removeFile(index) {
        this.uploadedFiles.splice(index, 1);
        this.displayUploadedFiles();
        this.updateCreateButton();
    }
    
    updateCreateButton() {
        const createBtn = document.getElementById('create-btn');
        createBtn.disabled = this.uploadedFiles.length === 0;
    }
    
    // 配置管理
    async loadConfig() {
        try {
            const response = await fetch('/api/config');
            const result = await response.json();
            
            this.config = result.config;
            
            // 更新表单
            document.getElementById('bot-token').value = this.config.TELEGRAM_BOT_TOKEN || '';
            document.getElementById('user-id').value = this.config.TELEGRAM_USER_ID || '';
            document.getElementById('pack-prefix').value = this.config.PACK_NAME_PREFIX || '';
            document.getElementById('default-emoji-config').value = this.config.DEFAULT_EMOJI || '😀';
            document.getElementById('default-emoji').value = this.config.DEFAULT_EMOJI || '😀';
            
            // 更新代理设置
            this.loadProxyConfig(this.config);
            
            // 更新状态
            this.updateBotStatus(result.bot_valid, result.bot_info);
            
        } catch (error) {
            this.showAlert('加载配置失败: ' + error.message, 'danger');
        }
    }
    
    async saveConfig(e) {
        e.preventDefault();
        
        const configData = {
            TELEGRAM_BOT_TOKEN: document.getElementById('bot-token').value.trim(),
            TELEGRAM_USER_ID: document.getElementById('user-id').value.trim(),
            PACK_NAME_PREFIX: document.getElementById('pack-prefix').value.trim(),
            DEFAULT_EMOJI: document.getElementById('default-emoji-config').value.trim() || '😀',
            ...this.getProxyConfig()
        };
        
        // 验证代理配置
        if (!this.validateProxyConfig(configData)) {
            return;
        }
        
        try {
            this.showLoading(true);
            const response = await fetch('/api/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(configData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.config = configData;
                this.updateBotStatus(true, result.bot_info);
                this.showAlert('配置保存成功!', 'success');
            } else {
                this.showAlert('保存失败: ' + result.error, 'danger');
            }
        } catch (error) {
            this.showAlert('保存失败: ' + error.message, 'danger');
        } finally {
            this.showLoading(false);
        }
    }
    
    async testConfig() {
        const botToken = document.getElementById('bot-token').value.trim();
        
        if (!botToken) {
            this.showAlert('请先输入 Bot Token', 'warning');
            return;
        }
        
        try {
            this.showLoading(true);
            const response = await fetch('/api/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    TELEGRAM_BOT_TOKEN: botToken,
                    TELEGRAM_USER_ID: document.getElementById('user-id').value.trim() || '0',
                    PACK_NAME_PREFIX: '',
                    DEFAULT_EMOJI: '😀'
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showAlert(`连接成功! Bot: @${result.bot_info.username}`, 'success');
                this.updateBotStatus(true, result.bot_info);
            } else {
                this.showAlert('连接失败: ' + result.error, 'danger');
                this.updateBotStatus(false);
            }
        } catch (error) {
            this.showAlert('测试失败: ' + error.message, 'danger');
            this.updateBotStatus(false);
        } finally {
            this.showLoading(false);
        }
    }
    
    updateBotStatus(isValid, botInfo = null) {
        const statusIcon = document.getElementById('bot-status').querySelector('i');
        const infoText = document.getElementById('bot-info');
        const configWarning = document.getElementById('config-warning');
        
        if (isValid && botInfo) {
            statusIcon.className = 'bi bi-circle-fill text-success';
            infoText.textContent = `已连接: @${botInfo.username}`;
            // 隐藏配置警告
            if (configWarning) {
                configWarning.classList.add('d-none');
            }
        } else {
            statusIcon.className = 'bi bi-circle-fill text-danger';
            infoText.textContent = '未配置或连接失败';
            // 显示配置警告
            if (configWarning) {
                configWarning.classList.remove('d-none');
            }
        }
    }
    
    // 表情包创建
    async createStickerPack(e) {
        e.preventDefault();
        
        if (this.uploadedFiles.length === 0) {
            this.showAlert('请先上传文件', 'warning');
            return;
        }
        
        if (!this.config.TELEGRAM_BOT_TOKEN || !this.config.TELEGRAM_USER_ID) {
            this.showAlert('请先配置 Bot Token 和用户 ID', 'warning');
            this.switchTab('config');
            return;
        }
        
        const packData = {
            pack_name: document.getElementById('pack-name').value.trim(),
            pack_title: document.getElementById('pack-title').value.trim(),
            files: this.uploadedFiles,
            emojis: this.getEmojiList()
        };
        
        try {
            this.showLoading(true);
            const response = await fetch('/api/create-sticker-pack', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(packData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.currentTask = result.task_id;
                this.showProgressCard(true);
                this.pollTaskStatus();
            } else {
                this.showAlert('创建失败: ' + result.error, 'danger');
            }
        } catch (error) {
            this.showAlert('创建失败: ' + error.message, 'danger');
        } finally {
            this.showLoading(false);
        }
    }
    
    getEmojiList() {
        const defaultEmoji = document.getElementById('default-emoji').value.trim() || '😀';
        return this.uploadedFiles.map(() => defaultEmoji);
    }
    
    showProgressCard(show) {
        const card = document.getElementById('progress-card');
        card.style.display = show ? 'block' : 'none';
        
        if (!show) {
            this.resetProgress();
        }
    }
    
    resetProgress() {
        document.getElementById('progress-bar').style.width = '0%';
        document.getElementById('progress-text').textContent = '等待开始...';
    }
    
    async pollTaskStatus() {
        if (!this.currentTask) return;
        
        try {
            const response = await fetch(`/api/task-status/${this.currentTask}`);
            const status = await response.json();
            
            this.updateProgress(status);
            
            if (status.status === 'processing' || status.status === 'starting') {
                setTimeout(() => this.pollTaskStatus(), 1000);
            } else if (status.status === 'completed') {
                this.handleTaskCompleted(status);
            } else if (status.status === 'error') {
                this.handleTaskError(status);
            }
        } catch (error) {
            this.showAlert('获取进度失败: ' + error.message, 'danger');
        }
    }
    
    updateProgress(status) {
        const progressBar = document.getElementById('progress-bar');
        const progressText = document.getElementById('progress-text');
        
        progressBar.style.width = `${status.progress}%`;
        progressText.textContent = `${status.message} (${Math.round(status.progress)}%)`;
    }
    
    handleTaskCompleted(status) {
        this.showAlert('表情包创建成功!', 'success');
        this.updateProgress({progress: 100, message: '完成!'});
        
        if (status.result && status.result.pack_url) {
            this.showAlert(`表情包链接: <a href="${status.result.pack_url}" target="_blank">${status.result.pack_url}</a>`, 'info');
        }
        
        setTimeout(() => {
            this.showProgressCard(false);
            this.resetForm();
        }, 3000);
    }
    
    handleTaskError(status) {
        this.showAlert('创建失败: ' + status.message, 'danger');
        this.showProgressCard(false);
    }
    
    resetForm() {
        document.getElementById('sticker-form').reset();
        document.getElementById('default-emoji').value = this.config.DEFAULT_EMOJI || '😀';
        this.uploadedFiles = [];
        this.displayUploadedFiles();
        this.updateCreateButton();
    }
    
    // 表情包管理
    async searchStickerPack() {
        const packName = document.getElementById('pack-search').value.trim();
        
        if (!packName) {
            this.showAlert('请输入表情包名称', 'warning');
            return;
        }
        
        if (!this.config.TELEGRAM_BOT_TOKEN) {
            this.showAlert('请先配置 Bot Token', 'warning');
            this.switchTab('config');
            return;
        }
        
        try {
            this.showLoading(true);
            const response = await fetch(`/api/sticker-pack/${encodeURIComponent(packName)}`);
            const result = await response.json();
            
            if (result.success) {
                this.displayStickerPack(result.pack);
            } else {
                this.showAlert('找不到表情包: ' + result.error, 'warning');
                this.hideStickerPack();
            }
        } catch (error) {
            this.showAlert('搜索失败: ' + error.message, 'danger');
            this.hideStickerPack();
        } finally {
            this.showLoading(false);
        }
    }
    
    displayStickerPack(pack) {
        document.getElementById('pack-placeholder').style.display = 'none';
        document.getElementById('pack-info').style.display = 'block';
        
        const packInfo = document.getElementById('pack-info');
        packInfo.innerHTML = `
            <div class="d-flex justify-content-between align-items-center mb-4">
                <div>
                    <h4>${pack.title}</h4>
                    <p class="text-muted mb-0">
                        ${pack.name} • ${pack.total_stickers} 个贴纸 • 
                        ${pack.is_animated ? '动画' : pack.is_video ? '视频' : '静态'}
                    </p>
                </div>
                <div>
                    <button class="btn btn-danger btn-sm delete-pack-btn" data-pack-name="${pack.name}">
                        <i class="bi bi-trash"></i> 删除表情包
                    </button>
                </div>
            </div>
            
            <div class="row">
                ${pack.stickers.map(sticker => `
                    <div class="col-md-6 col-lg-4 mb-3">
                        <div class="sticker-item">
                            <div class="d-flex align-items-center">
                                <div class="sticker-emoji me-3">
                                    ${sticker.emoji}
                                </div>
                                <div class="flex-grow-1">
                                    <div class="d-flex justify-content-between align-items-center">
                                        <small class="text-muted">位置 ${sticker.position}</small>
                                        <div>
                                            <button class="btn btn-sm btn-outline-primary me-1 edit-sticker-btn" 
                                                    data-pack-name="${pack.name}" 
                                                    data-file-id="${sticker.file_id}" 
                                                    data-emoji="${sticker.emoji}">
                                                <i class="bi bi-pencil"></i>
                                            </button>
                                            <button class="btn btn-sm btn-outline-danger delete-sticker-btn" 
                                                    data-pack-name="${pack.name}" 
                                                    data-file-id="${sticker.file_id}">
                                                <i class="bi bi-trash"></i>
                                            </button>
                                        </div>
                                    </div>
                                    <small class="text-muted d-block">${sticker.width}×${sticker.height}px</small>
                                    <small class="text-muted">${sticker.file_id.substring(0, 20)}...</small>
                                </div>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
        
        // 设置表情包管理事件
        this.setupStickerPackEvents();
    }
    
    // 表情包管理事件设置 - 新增方法
    setupStickerPackEvents() {
        const packInfo = document.getElementById('pack-info');
        
        // 移除旧的事件监听器
        packInfo.removeEventListener('click', this.handleStickerPackClick);
        
        // 添加新的事件监听器
        this.handleStickerPackClick = (e) => {
            const target = e.target.closest('button');
            if (!target) return;
            
            e.preventDefault();
            
            if (target.classList.contains('delete-pack-btn')) {
                const packName = target.dataset.packName;
                this.deleteStickerPack(packName);
            } else if (target.classList.contains('edit-sticker-btn')) {
                const packName = target.dataset.packName;
                const fileId = target.dataset.fileId;
                const emoji = target.dataset.emoji;
                this.editSticker(packName, fileId, emoji);
            } else if (target.classList.contains('delete-sticker-btn')) {
                const packName = target.dataset.packName;
                const fileId = target.dataset.fileId;
                this.deleteSticker(packName, fileId);
            }
        };
        
        packInfo.addEventListener('click', this.handleStickerPackClick);
    }
    
    hideStickerPack() {
        document.getElementById('pack-placeholder').style.display = 'block';
        document.getElementById('pack-info').style.display = 'none';
    }
    
    editSticker(packName, fileId, currentEmoji) {
        document.getElementById('edit-pack-name').value = packName;
        document.getElementById('edit-file-id').value = fileId;
        document.getElementById('edit-emoji-list').value = currentEmoji;
        
        const modal = new bootstrap.Modal(document.getElementById('editStickerModal'));
        modal.show();
    }
    
    async saveStickerEdit() {
        const packName = document.getElementById('edit-pack-name').value;
        const fileId = document.getElementById('edit-file-id').value;
        const emojiList = document.getElementById('edit-emoji-list').value.split(',').map(e => e.trim()).filter(e => e);
        
        if (emojiList.length === 0) {
            this.showAlert('请输入至少一个 emoji', 'warning');
            return;
        }
        
        try {
            this.showLoading(true);
            const response = await fetch(`/api/sticker-pack/${encodeURIComponent(packName)}/sticker/${encodeURIComponent(fileId)}/emoji`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({emoji_list: emojiList})
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showAlert('更新成功!', 'success');
                const modal = bootstrap.Modal.getInstance(document.getElementById('editStickerModal'));
                modal.hide();
                
                // 重新加载表情包信息
                setTimeout(() => this.searchStickerPack(), 500);
            } else {
                this.showAlert('更新失败: ' + result.error, 'danger');
            }
        } catch (error) {
            this.showAlert('更新失败: ' + error.message, 'danger');
        } finally {
            this.showLoading(false);
        }
    }
    
    async deleteSticker(packName, fileId) {
        if (!confirm('确定要删除这个贴纸吗？')) {
            return;
        }
        
        try {
            this.showLoading(true);
            const response = await fetch(`/api/sticker-pack/${encodeURIComponent(packName)}/sticker/${encodeURIComponent(fileId)}`, {
                method: 'DELETE'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showAlert('删除成功!', 'success');
                // 重新加载表情包信息
                setTimeout(() => this.searchStickerPack(), 500);
            } else {
                this.showAlert('删除失败: ' + result.error, 'danger');
            }
        } catch (error) {
            this.showAlert('删除失败: ' + error.message, 'danger');
        } finally {
            this.showLoading(false);
        }
    }
    
    async deleteStickerPack(packName) {
        if (!confirm('确定要删除整个表情包吗？此操作无法撤销！')) {
            return;
        }
        
        const confirmText = prompt('请输入 "DELETE" 确认删除:');
        if (confirmText !== 'DELETE') {
            this.showAlert('已取消删除', 'info');
            return;
        }
        
        try {
            this.showLoading(true);
            const response = await fetch(`/api/sticker-pack/${encodeURIComponent(packName)}`, {
                method: 'DELETE'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showAlert('表情包删除成功!', 'success');
                this.hideStickerPack();
                document.getElementById('pack-search').value = '';
            } else {
                this.showAlert('删除失败: ' + result.error, 'danger');
            }
        } catch (error) {
            this.showAlert('删除失败: ' + error.message, 'danger');
        } finally {
            this.showLoading(false);
        }
    }
    
    // 代理设置相关方法
    toggleProxySettings(e) {
        const proxySettings = document.getElementById('proxy-settings');
        proxySettings.style.display = e.target.checked ? 'block' : 'none';
    }
    
    toggleProxyAuth(e) {
        const proxyAuthSettings = document.getElementById('proxy-auth-settings');
        proxyAuthSettings.style.display = e.target.checked ? 'block' : 'none';
    }
    
    loadProxyConfig(config) {
        // 加载代理配置到表单
        const proxyEnabled = config.PROXY_ENABLED === 'true';
        document.getElementById('proxy-enabled').checked = proxyEnabled;
        
        if (proxyEnabled) {
            document.getElementById('proxy-settings').style.display = 'block';
            document.getElementById('proxy-type').value = config.PROXY_TYPE || 'http';
            document.getElementById('proxy-host').value = config.PROXY_HOST || '';
            document.getElementById('proxy-port').value = config.PROXY_PORT || '';
            
            const authEnabled = config.PROXY_AUTH_ENABLED === 'true';
            document.getElementById('proxy-auth-enabled').checked = authEnabled;
            
            if (authEnabled) {
                document.getElementById('proxy-auth-settings').style.display = 'block';
                document.getElementById('proxy-username').value = config.PROXY_USERNAME || '';
                document.getElementById('proxy-password').value = config.PROXY_PASSWORD || '';
            }
        }
    }
    
    getProxyConfig() {
        const proxyEnabled = document.getElementById('proxy-enabled').checked;
        
        if (!proxyEnabled) {
            return {
                PROXY_ENABLED: 'false'
            };
        }
        
        const authEnabled = document.getElementById('proxy-auth-enabled').checked;
        
        const proxyConfig = {
            PROXY_ENABLED: 'true',
            PROXY_TYPE: document.getElementById('proxy-type').value,
            PROXY_HOST: document.getElementById('proxy-host').value.trim(),
            PROXY_PORT: document.getElementById('proxy-port').value.trim(),
            PROXY_AUTH_ENABLED: authEnabled ? 'true' : 'false'
        };
        
        if (authEnabled) {
            proxyConfig.PROXY_USERNAME = document.getElementById('proxy-username').value.trim();
            proxyConfig.PROXY_PASSWORD = document.getElementById('proxy-password').value.trim();
        }
        
        return proxyConfig;
    }
    
    validateProxyConfig(proxyConfig) {
        if (proxyConfig.PROXY_ENABLED === 'true') {
            if (!proxyConfig.PROXY_HOST) {
                this.showAlert('代理服务器地址不能为空', 'warning');
                return false;
            }
            
            if (!proxyConfig.PROXY_PORT || isNaN(proxyConfig.PROXY_PORT)) {
                this.showAlert('代理端口必须是有效数字', 'warning');
                return false;
            }
            
            const port = parseInt(proxyConfig.PROXY_PORT);
            if (port < 1 || port > 65535) {
                this.showAlert('代理端口必须在1-65535之间', 'warning');
                return false;
            }
            
            if (proxyConfig.PROXY_AUTH_ENABLED === 'true') {
                if (!proxyConfig.PROXY_USERNAME) {
                    this.showAlert('启用认证时用户名不能为空', 'warning');
                    return false;
                }
                
                if (!proxyConfig.PROXY_PASSWORD) {
                    this.showAlert('启用认证时密码不能为空', 'warning');
                    return false;
                }
            }
        }
        
        return true;
    }
    
    // 通用工具方法
    showAlert(message, type = 'info') {
        const alertContainer = document.getElementById('alert-container');
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        alertContainer.appendChild(alert);
        
        // 自动关闭
        setTimeout(() => {
            if (alert.parentNode) {
                alert.classList.add('fade-out');
                setTimeout(() => alert.remove(), 300);
            }
        }, 5000);
    }
    
    showLoading(show) {
        // 简单的加载状态，可以扩展为全局加载遮罩
        document.body.style.cursor = show ? 'wait' : 'default';
    }
}

// 全局变量和函数
let stickerMaker;

// 全局switchTab函数，供HTML调用
function switchTab(tabName) {
    if (stickerMaker) {
        stickerMaker.switchTab(tabName);
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    stickerMaker = new StickerMaker();
});