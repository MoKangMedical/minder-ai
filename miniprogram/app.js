App({
  globalData: {
    userInfo: null,
    token: null,
    baseUrl: 'http://localhost:8004/api/v1'
  },

  onLaunch() {
    this.checkLogin();
  },

  checkLogin() {
    const token = wx.getStorageSync('token');
    const userInfo = wx.getStorageSync('userInfo');
    if (token && userInfo) {
      this.globalData.token = token;
      this.globalData.userInfo = userInfo;
    }
  },

  login() {
    return new Promise((resolve, reject) => {
      wx.login({
        success: (res) => {
          if (res.code) {
            wx.request({
              url: `${this.globalData.baseUrl}/auth/wechat-login`,
              method: 'POST',
              data: { code: res.code },
              success: (resp) => {
                if (resp.statusCode === 200 && resp.data.access_token) {
                  this.globalData.token = resp.data.access_token;
                  this.globalData.userInfo = resp.data.user;
                  wx.setStorageSync('token', resp.data.access_token);
                  wx.setStorageSync('userInfo', resp.data.user);
                  resolve(resp.data);
                } else {
                  // Mock login for development
                  this._mockLogin(resolve);
                }
              },
              fail: () => {
                this._mockLogin(resolve);
              }
            });
          } else {
            reject(new Error('登录失败'));
          }
        },
        fail: reject
      });
    });
  },

  _mockLogin(resolve) {
    const mockUser = {
      id: 1,
      nickname: '小明',
      avatar: '',
      gender: 'male',
      age: 28,
      city: '北京',
      vip_level: 0
    };
    const mockToken = 'mock_token_' + Date.now();
    this.globalData.token = mockToken;
    this.globalData.userInfo = mockUser;
    wx.setStorageSync('token', mockToken);
    wx.setStorageSync('userInfo', mockUser);
    resolve({ access_token: mockToken, user: mockUser });
  }
});
