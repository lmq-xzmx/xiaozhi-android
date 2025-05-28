package info.dourok.voicebot

import android.app.Application
import android.util.Log
import dagger.hilt.android.HiltAndroidApp
import info.dourok.voicebot.data.model.DeviceIdManager
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltAndroidApp
class VApplication : Application() {
    
    companion object {
        private const val TAG = "VApplication"
    }
    
    @Inject
    lateinit var deviceIdManager: DeviceIdManager
    
    // 应用级协程作用域
    private val applicationScope = CoroutineScope(SupervisorJob() + Dispatchers.Main)
    
    override fun onCreate() {
        super.onCreate()
        
        Log.i(TAG, "VApplication 启动")
        
        // 设置全局异常处理器
        setupGlobalExceptionHandler()
        
        // 预加载关键组件（在后台线程）
        preloadCriticalComponents()
        
        Log.i(TAG, "VApplication 初始化完成")
    }
    
    /**
     * 设置全局异常处理器
     */
    private fun setupGlobalExceptionHandler() {
        val defaultHandler = Thread.getDefaultUncaughtExceptionHandler()
        
        Thread.setDefaultUncaughtExceptionHandler { thread, exception ->
            Log.e(TAG, "💥 全局未捕获异常", exception)
            
            // 记录关键信息
            Log.e(TAG, "线程: ${thread.name}")
            Log.e(TAG, "异常类型: ${exception.javaClass.simpleName}")
            Log.e(TAG, "异常消息: ${exception.message}")
            
            // 如果是启动阶段的关键异常，尝试记录更多信息
            if (exception is RuntimeException || exception is Error) {
                Log.e(TAG, "这可能是启动阶段的关键异常")
                
                // 检查是否是依赖注入相关的异常
                val stackTrace = exception.stackTraceToString()
                when {
                    stackTrace.contains("Hilt") -> {
                        Log.e(TAG, "🔧 Hilt依赖注入异常，检查@Inject注解和模块配置")
                    }
                    stackTrace.contains("DataStore") -> {
                        Log.e(TAG, "💾 DataStore异常，检查数据存储操作")
                    }
                    stackTrace.contains("ViewModel") -> {
                        Log.e(TAG, "🎭 ViewModel异常，检查ViewModel构造函数")
                    }
                    stackTrace.contains("Compose") -> {
                        Log.e(TAG, "🎨 Compose异常，检查UI组件")
                    }
                    else -> {
                        Log.e(TAG, "❓ 其他类型异常")
                    }
                }
            }
            
            // 调用默认处理器
            defaultHandler?.uncaughtException(thread, exception)
        }
        
        Log.i(TAG, "✅ 全局异常处理器已设置")
    }
    
    /**
     * 预加载关键组件
     */
    private fun preloadCriticalComponents() {
        applicationScope.launch {
            try {
                Log.d(TAG, "开始预加载关键组件")
                
                // 预加载设备ID（这是最重要的，很多组件都依赖它）
                deviceIdManager.preloadDeviceId()
                
                Log.i(TAG, "✅ 关键组件预加载完成")
                
            } catch (e: Exception) {
                Log.w(TAG, "⚠️ 关键组件预加载失败，但不影响应用启动", e)
                
                // 预加载失败不应该阻止应用启动
                // 组件会在实际使用时进行懒加载
            }
        }
    }
    
    override fun onTerminate() {
        Log.i(TAG, "VApplication 终止")
        super.onTerminate()
    }
    
    override fun onLowMemory() {
        Log.w(TAG, "VApplication 内存不足警告")
        super.onLowMemory()
        
        // 可以在这里清理一些缓存
        try {
            // 清理设备ID缓存以外的其他缓存
            Log.d(TAG, "清理非关键缓存以释放内存")
        } catch (e: Exception) {
            Log.w(TAG, "清理缓存时发生异常", e)
        }
    }
}