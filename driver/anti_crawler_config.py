# === 反爬虫配置文件 ===
"""
反爬虫配置模块
包含浏览器指纹伪装、JavaScript 注入脚本、HTTP 头配置等
"""

import random
import os
import uuid
from typing import Dict, List, Optional, Any

from driver.user_agent import UserAgentGenerator


class AntiCrawlerConfig:
    """反爬虫配置管理类"""
    
    def __init__(self):
        self._ua_generator = UserAgentGenerator()
    
    # ========== HTTP 请求头配置 ==========
    
    HEADERS = {
        'accept': [
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8"
        ],
        'accept_language': [
            "zh-CN,zh;q=0.9,en;q=0.8",
            "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
            "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
        ],
        'cache_control': ["no-cache", "max-age=0", "no-store"]
    }
    
    # 时区配置
    TIMEZONES = [
        "Asia/Shanghai",
        "Asia/Beijing", 
        "Asia/Hong_Kong",
        "Asia/Taipei"
    ]
    
    # 语言配置
    LOCALES = [
        "zh-CN",
        "zh-TW", 
        "zh-HK"
    ]
    
    # ========== 配置生成方法 ==========
    
    def get_anti_crawler_config(self, mobile_mode: bool = False) -> Dict[str, Any]:
        """
        获取反爬虫配置（对应 PlaywrightController._get_anti_crawler_config）
        
        Args:
            mobile_mode: 是否为移动端模式
            
        Returns:
            Playwright context 配置字典
        """
        # 生成随机指纹
        fingerprint = self._generate_uuid()
        
        # 基础配置
        config = {
            "user_agent": self._ua_generator.get_realistic_user_agent(mobile_mode),
            "viewport": {
                "width": random.randint(1200, 1920) if not mobile_mode else 375,
                "height": random.randint(800, 1080) if not mobile_mode else 812,
                "device_scale_factor": random.choice([1, 1.25, 1.5, 2])
            },
            "java_script_enabled": True,
            "ignore_https_errors": True,
            "bypass_csp": True,
            "extra_http_headers": self._get_http_headers(mobile_mode),
            "permissions": [],
        }
        
        # 移动端特殊配置
        if mobile_mode:
            config["extra_http_headers"].update({
                "User-Agent": config["user_agent"],
                "X-Requested-With": "com.tencent.mm"
            })
        
        return config
    
    def _get_http_headers(self, mobile_mode: bool = False) -> Dict[str, str]:
        """获取 HTTP 请求头"""
        headers = {
            "Accept": random.choice(self.HEADERS['accept']),
            "Accept-Language": random.choice(self.HEADERS['accept_language']),
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": random.choice(self.HEADERS['cache_control']),
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
        }
        
        if mobile_mode:
            headers["X-Requested-With"] = "com.tencent.mm"
        
        return headers
    
    def _generate_uuid(self) -> str:
        """生成 UUID 指纹"""
        return str(uuid.uuid4()).replace("-", "")
    
    # ========== JavaScript 反爬虫脚本 ==========
    
    @staticmethod
    def get_init_script() -> str:
        """
        获取初始化注入脚本（对应 PlaywrightController._apply_anti_crawler_scripts 的 add_init_script）
        
        Returns:
            JavaScript 代码字符串
        """
        return """
        // ========== 禁用 WebDriver 检测 ==========
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
            configurable: true
        });
        
        // ========== 禁用 Chrome 自动化标志 ==========
        Object.defineProperty(navigator, 'plugins', {
            get: () => {
                const plugins = [
                    { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
                    { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
                    { name: 'Native Client', filename: 'internal-nacl-plugin' }
                ];
                plugins.item = (i) => plugins[i] || null;
                plugins.namedItem = (name) => plugins.find(p => p.name === name) || null;
                plugins.refresh = () => {};
                return plugins;
            }
        });
        
        Object.defineProperty(navigator, 'languages', {
            get: () => ['zh-CN', 'zh', 'en-US', 'en']
        });
        
        // ========== 禁用 WebRTC（防止 IP 泄露）==========
        if (window.RTCPeerConnection) {
            window.RTCPeerConnection = undefined;
        }
        if (window.webkitRTCPeerConnection) {
            window.webkitRTCPeerConnection = undefined;
        }
        
        // ========== 禁用 Canvas 指纹 ==========
        const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function(type) {
            if (type === 'image/png' && this.width === 220 && this.height === 30) {
                // 检测到指纹采集，返回空白
                return 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==';
            }
            // 添加随机噪声
            const context = this.getContext('2d');
            if (context) {
                const imageData = context.getImageData(0, 0, this.width, this.height);
                for (let i = 0; i < imageData.data.length; i += 4) {
                    imageData.data[i] ^= (Math.random() * 2) | 0;
                }
                context.putImageData(imageData, 0, 0);
            }
            return originalToDataURL.apply(this, arguments);
        };
        
        // ========== 禁用 AudioContext 指纹 ==========
        const audioContext = window.AudioContext || window.webkitAudioContext;
        if (audioContext) {
            const originalCreateAnalyser = audioContext.prototype.createAnalyser;
            audioContext.prototype.createAnalyser = function() {
                const analyser = originalCreateAnalyser.apply(this, arguments);
                const originalGetFloatFrequencyData = analyser.getFloatFrequencyData;
                analyser.getFloatFrequencyData = function(array) {
                    // 返回随机噪声而非真实音频指纹
                    for (let i = 0; i < array.length; i++) {
                        array[i] = -100 + Math.random() * 50;
                    }
                };
                return analyser;
            };
        }
        
        // ========== 禁用 WebGL 指纹 ==========
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) return 'Intel Inc.';  // UNMASKED_VENDOR_WEBGL
            if (parameter === 37446) return 'Intel Iris OpenGL Engine';  // UNMASKED_RENDERER_WEBGL
            return getParameter.apply(this, arguments);
        };
        
        if (typeof WebGL2RenderingContext !== 'undefined') {
            const getParameter2 = WebGL2RenderingContext.prototype.getParameter;
            WebGL2RenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) return 'Intel Inc.';
                if (parameter === 37446) return 'Intel Iris OpenGL Engine';
                return getParameter2.apply(this, arguments);
            };
        }
        
        // ========== 禁用字体指纹 ==========
        const originalMeasureText = CanvasRenderingContext2D.prototype.measureText;
        CanvasRenderingContext2D.prototype.measureText = function(text) {
            const result = originalMeasureText.apply(this, arguments);
            // 添加微小随机偏移
            result.width += Math.random() * 0.1 - 0.05;
            return result;
        };
        
        // ========== 修改 permissions API ==========
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        
        // ========== 禁用 Battery API ==========
        if (navigator.getBattery) {
            navigator.getBattery = () => Promise.resolve({
                charging: true,
                chargingTime: 0,
                dischargingTime: Infinity,
                level: 1
            });
        }
        
        // ========== 禁用 Network Information API ==========
        if (navigator.connection) {
            Object.defineProperty(navigator, 'connection', {
                get: () => ({
                    effectiveType: '4g',
                    downlink: 10,
                    rtt: 50,
                    saveData: false
                })
            });
        }
        
        // ========== 隐藏自动化框架痕迹 ==========
        delete window.__playwright;
        delete window.__puppeteer;
        delete window.__selenium;
        delete window.__webdriver_evaluate;
        delete window.__selenium_evaluate;
        delete window.__fxdriver_evaluate;
        delete window.__driver_unwrapped;
        delete window.__webdriver_unwrapped;
        delete window.__selenium_unwrapped;
        delete window.__fxdriver_unwrapped;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
        
        console.log('[反检测] 用户特征保护已启用');
        """
    
    @staticmethod
    def get_behavior_script() -> str:
        """
        获取浏览器行为模拟脚本（对应 PlaywrightController._apply_anti_crawler_scripts 的 evaluate）
        
        Returns:
            JavaScript 代码字符串
        """
        return """
        // 随机延迟点击事件
        const originalAddEventListener = EventTarget.prototype.addEventListener;
        EventTarget.prototype.addEventListener = function(type, listener, options) {
            if (type === 'click') {
                const wrappedListener = function(...args) {
                    setTimeout(() => listener.apply(this, args), Math.random() * 100 + 50);
                };
                return originalAddEventListener.call(this, type, wrappedListener, options);
            }
            return originalAddEventListener.call(this, type, listener, options);
        };
        
        // 随机化鼠标移动
        document.addEventListener('mousemove', (e) => {
            if (Math.random() > 0.7) {
                e.stopImmediatePropagation();
            }
        }, true);
        """
    
    # ========== 视口配置 ==========
    
    @staticmethod
    def get_viewport(mobile_mode: bool = False) -> Dict[str, int]:
        """获取视口配置"""
        if mobile_mode:
            return {"width": 375, "height": 812}
        return {
            "width": random.randint(1200, 1920),
            "height": random.randint(800, 1080)
        }
    
    @staticmethod
    def get_device_scale_factor() -> float:
        """获取设备缩放因子"""
        return random.choice([1.0, 1.25, 1.5, 2.0])


# 环境变量配置
ENV_CONFIG = {
    "ENABLE_STEALTH": os.getenv("ENABLE_STEALTH", "true").lower() == "true",
    "ENABLE_BEHAVIOR_SIMULATION": os.getenv("ENABLE_BEHAVIOR_SIMULATION", "true").lower() == "true",
    "ENABLE_ADVANCED_DETECTION": os.getenv("ENABLE_ADVANCED_DETECTION", "true").lower() == "true",
    "DETECTION_SENSITIVITY": float(os.getenv("DETECTION_SENSITIVITY", "0.8")),
    "MAX_DETECTION_ATTEMPTS": int(os.getenv("MAX_DETECTION_ATTEMPTS", "10")),
    "BEHAVIOR_SIMULATION_INTERVAL": int(os.getenv("BEHAVIOR_SIMULATION_INTERVAL", "2000")),
    "RANDOM_DELAY_MIN": int(os.getenv("RANDOM_DELAY_MIN", "100")),
    "RANDOM_DELAY_MAX": int(os.getenv("RANDOM_DELAY_MAX", "500"))
}


# 全局实例
_anti_crawler_config = AntiCrawlerConfig()


def get_anti_crawler_config(mobile_mode: bool = False) -> Dict[str, Any]:
    """获取反爬虫配置（便捷函数）"""
    return _anti_crawler_config.get_anti_crawler_config(mobile_mode)


def get_init_script() -> str:
    """获取初始化注入脚本（便捷函数）"""
    return AntiCrawlerConfig.get_init_script()


def get_behavior_script() -> str:
    """获取行为模拟脚本（便捷函数）"""
    return AntiCrawlerConfig.get_behavior_script()
