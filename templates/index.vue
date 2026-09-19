<template>
	<view class="content">
		<!-- Logo区域 -->
		<image class="logo" src="/static/wunsun-logo.png" mode="widthFix"></image>
		
		<!-- 标题 -->
		<view class="title-area">
			<text class="title">AI数据分析助手</text>
			<text class="subtitle">智能数据分析，助力决策</text>
		</view>
		
		<!-- 登录表单 -->
		<view class="form-container">
			<!-- 邮箱输入 -->
			<view class="input-group">
				<text class="label">邮箱地址</text>
				<input 
					class="input" 
					v-model="email" 
					type="text" 
					placeholder="请输入您的邮箱"
					placeholder-class="placeholder"
				/>
			</view>
			
			<!-- 验证码输入 -->
			<view class="input-group">
				<text class="label">验证码</text>
				<view class="code-input-wrapper">
					<input 
						class="input code-input" 
						v-model="code" 
						type="number" 
						maxlength="4"
						placeholder="请输入验证码"
						placeholder-class="placeholder"
					/>
					<button 
						class="code-btn" 
						:class="{'code-btn-disabled': countdown > 0}"
						@click="sendCode"
						:disabled="countdown > 0 || !email"
					>
						{{ countdown > 0 ? `${countdown}s` : '获取验证码' }}
					</button>
				</view>
			</view>
			
			<!-- 登录按钮 -->
			<button class="login-btn" @click="handleLogin" :disabled="!email || !code">
				登录
			</button>
		</view>
	</view>
</template>

<script>
	// 修复：后端实际端口是 8000
	const BASE_URL = 'http://localhost:8000'
	
	export default {
		data() {
			return {
				email: '',
				code: '',
				countdown: 0,
				timer: null
			}
		},
		onUnload() {
			// 清除定时器
			if (this.timer) {
				clearInterval(this.timer)
			}
		},
		methods: {
			// 验证邮箱格式
			validateEmail(email) {
				const reg = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/
				return reg.test(email)
			},
			
			// 发送验证码
			sendCode() {
				// 验证邮箱
				if (!this.email) {
					uni.showToast({
						title: '请输入邮箱',
						icon: 'none'
					})
					return
				}
				
				if (!this.validateEmail(this.email)) {
					uni.showToast({
						title: '请输入正确的邮箱格式',
						icon: 'none'
					})
					return
				}
				
				// 发送验证码请求
				uni.request({
					url: BASE_URL + '/send_code',
					method: 'POST',
					header: {
						'Content-Type': 'application/json'
					},
					data: {
						email: this.email
					},
					success: (res) => {
						if (res.data.code === 200) {
							uni.showToast({
								title: '验证码已发送',
								icon: 'success'
							})
							// 开始倒计时
							this.countdown = 60
							this.timer = setInterval(() => {
								this.countdown--
								if (this.countdown <= 0) {
									clearInterval(this.timer)
								}
							}, 1000)
						} else {
							uni.showToast({
								title: res.data.msg || '发送失败',
								icon: 'none'
							})
						}
					},
					fail: () => {
						uni.showToast({
							title: '网络请求失败',
							icon: 'none'
						})
					}
				})
			},
			
			// 处理登录
			handleLogin() {
				// 验证邮箱
				if (!this.email) {
					uni.showToast({
						title: '请输入邮箱',
						icon: 'none'
					})
					return
				}
				
				// 验证验证码
				if (!this.code) {
					uni.showToast({
						title: '请输入验证码',
						icon: 'none'
					})
					return
				}
				
				// 发送登录请求
				uni.request({
					url: BASE_URL + '/login',
					method: 'POST',
					header: {
						'Content-Type': 'application/json'
					},
					data: {
						email: this.email,
						code: this.code
					},
					success: (res) => {
						if (res.data.code === 200) {
							// 保存登录信息
							uni.setStorageSync('userInfo', {
								email: this.email,
								token: 'mock_token_' + Date.now()
							})
							
							uni.showToast({
								title: '登录成功',
								icon: 'success'
							})
							
							// 跳转到聊天页面
							setTimeout(() => {
								uni.reLaunch({
									url: '/pages/chat/chat'
								})
							}, 1500)
						} else {
							uni.showToast({
								title: res.data.msg || '登录失败',
								icon: 'none'
							})
						}
					},
					fail: () => {
						uni.showToast({
							title: '网络请求失败',
							icon: 'none'
						})
					}
				})
			}
		}
	}
</script>

<style scoped>
	.content {
		display: flex;
		flex-direction: column;
		align-items: center;
		padding-top: 200rpx;
		background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
		min-height: 100vh;
	}
	
	.logo {
		width: 200rpx;
		margin-bottom: 60rpx;
	}
	
	.title-area {
		display: flex;
		flex-direction: column;
		align-items: center;
		margin-bottom: 80rpx;
	}
	
	.title {
		font-size: 48rpx;
		font-weight: bold;
		color: #fff;
		margin-bottom: 20rpx;
	}
	
	.subtitle {
		font-size: 28rpx;
		color: rgba(255, 255, 255, 0.8);
	}
	
	.form-container {
		width: 600rpx;
		background-color: #fff;
		border-radius: 30rpx;
		padding: 60rpx 40rpx;
		box-shadow: 0 10rpx 40rpx rgba(0, 0, 0, 0.2);
	}
	
	.input-group {
		margin-bottom: 40rpx;
	}
	
	.label {
		display: block;
		font-size: 28rpx;
		color: #333;
		margin-bottom: 20rpx;
		font-weight: 500;
	}
	
	.input {
		width: 100%;
		height: 90rpx;
		background-color: #f5f5f5;
		border-radius: 20rpx;
		padding: 0 30rpx;
		font-size: 28rpx;
	}
	
	.code-input-wrapper {
		display: flex;
		align-items: center;
		justify-content: space-between;
	}
	
	.code-input {
		width: 350rpx;
	}
	
	.code-btn {
		width: 180rpx;
		height: 90rpx;
		background-color: #667eea;
		color: #fff;
		border-radius: 20rpx;
		font-size: 26rpx;
		display: flex;
		align-items: center;
		justify-content: center;
		border: none;
	}
	
	.code-btn-disabled {
		background-color: #ccc;
	}
	
	.login-btn {
		width: 100%;
		height: 100rpx;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: #fff;
		border-radius: 50rpx;
		font-size: 32rpx;
		font-weight: bold;
		display: flex;
		align-items: center;
		justify-content: center;
		margin-top: 40rpx;
		border: none;
	}
	
	.login-btn[disabled] {
		background: #ccc;
	}
	
	.placeholder {
		color: #999;
	}
</style>
