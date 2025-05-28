package info.dourok.voicebot

import android.app.Application
import android.content.Context
import android.content.SharedPreferences
import android.content.res.Resources
import android.net.ConnectivityManager
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import info.dourok.voicebot.data.model.DeviceInfo
import info.dourok.voicebot.data.model.DummyDataGenerator
import info.dourok.voicebot.data.model.fromJsonToDeviceInfo
import info.dourok.voicebot.data.model.toJson
import info.dourok.voicebot.data.model.DeviceIdManager
import info.dourok.voicebot.config.DeviceConfigManager
import info.dourok.voicebot.binding.BindingStatusChecker
import javax.inject.Singleton
import androidx.core.content.edit
import dagger.hilt.EntryPoint
import dagger.hilt.android.components.ActivityComponent
import dagger.hilt.android.scopes.ActivityScoped
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.runBlocking
import javax.inject.Qualifier

@Module
@InstallIn(SingletonComponent::class)
object AppModule {
    @Provides
    @Singleton
    fun provideSharedPreferences(application: Application): SharedPreferences {
        return application.getSharedPreferences("app_prefs", Context.MODE_PRIVATE)
    }

    @Provides
    @Singleton
    fun provideApplicationContext(application: Application): Context {
        return application.applicationContext
    }

    @Provides
    @Singleton
    fun provideResources(application: Application): Resources {
        return application.resources
    }

    @Provides
    @Singleton
    fun provideConnectivityManager(application: Application): ConnectivityManager {
        return application.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
    }

    @Provides
    @Singleton
    fun provideDeviceIdManager(context: Context): DeviceIdManager {
        return DeviceIdManager(context)
    }

    @Provides
    @Singleton
    fun provideDeviceInfo(
        sp: SharedPreferences,
        deviceIdManager: DeviceIdManager
    ): DeviceInfo {
        sp.getString("device_id", null)?.let {
            try {
                val deviceInfo = fromJsonToDeviceInfo(it)
                // 检查是否使用了旧的固定MAC地址，如果是则标记需要更新
                if (deviceInfo.mac_address == "00:11:22:33:44:55") {
                    println("检测到旧的固定MAC地址，将在后台更新...")
                    // 不在这里阻塞，而是返回一个临时的设备信息
                    // 实际更新将在后台进行
                    return DummyDataGenerator.generateSync(deviceIdManager)
                }
                return deviceInfo
            } catch (e: Exception) {
                println("解析存储的设备信息失败，使用默认配置: ${e.message}")
            }
        }
        
        // 返回同步生成的设备信息，避免阻塞
        return DummyDataGenerator.generateSync(deviceIdManager)
    }

    @Provides
    @Singleton
    fun provideDeviceConfigManager(
        context: Context,
        deviceIdManager: DeviceIdManager
    ): DeviceConfigManager {
        return DeviceConfigManager(context, deviceIdManager)
    }

    @Provides
    @Singleton
    fun provideBindingStatusChecker(
        deviceConfigManager: DeviceConfigManager,
        context: Context
    ): BindingStatusChecker {
        return BindingStatusChecker(deviceConfigManager, context)
    }

    @Provides
    @Singleton
    @ApplicationScope
    fun provideCoroutineScope(
        @DefaultDispatcher defaultDispatcher: CoroutineDispatcher
    ): CoroutineScope = CoroutineScope(SupervisorJob() + defaultDispatcher)

    @DefaultDispatcher
    @Provides
    fun providesDefaultDispatcher(): CoroutineDispatcher = Dispatchers.Default

}

@Module
@InstallIn(SingletonComponent::class)
object NavigationModule {
    @Provides
    @Singleton
    @NavigationEvents
    fun provideNavigationEvents(): MutableSharedFlow<String> {
        return MutableSharedFlow(extraBufferCapacity = 1)
    }
}

@EntryPoint
@InstallIn(ActivityComponent::class)
interface NavigationEntryPoint {
    @NavigationEvents
    fun getNavigationEvents(): MutableSharedFlow<String>
}

@Retention(AnnotationRetention.RUNTIME)
@Qualifier
annotation class NavigationEvents


@Retention(AnnotationRetention.RUNTIME)
@Qualifier
annotation class ApplicationScope

@Retention(AnnotationRetention.RUNTIME)
@Qualifier
annotation class DefaultDispatcher