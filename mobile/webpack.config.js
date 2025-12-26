const webpack = require("@nativescript/webpack");
const { resolve } = require("path");

module.exports = (env) => {
	webpack.init(env);

	// Learn how to customize:
	// https://docs.nativescript.org/webpack

	webpack.chainWebpack((config) => {
		// 添加路径别名解析
		config.resolve.alias.set("@shared", resolve(__dirname, "../packages/shared"));
		config.resolve.alias.set("@device-monitor/shared", resolve(__dirname, "../packages/shared"));
	});

	return webpack.resolveConfig();
};
