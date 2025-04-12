//===================================依赖 crypto-js.js=======================
const comKey = CryptoJS.enc.Utf8.parse("WxtEWkge01KKC6QB"); //十六位十六进制数作为密钥
const comIntegrity = "0123456789ABCDEF";
class AesUtil {
	constructor() {

	}
	encrypt({
		data,
		enableIntegrity=true//是否激活完整性校验
	}) {
		if (enableIntegrity) {
			data += "#" + comIntegrity;
		}
		let dataEncode = CryptoJS.enc.Utf8.parse(data);
		let encrypted = CryptoJS.AES.encrypt(dataEncode, comKey, {
			mode: CryptoJS.mode.ECB,
			padding: CryptoJS.pad.Pkcs7
		});
		return  CryptoJS.enc.Base64.stringify(encrypted.ciphertext);
	}
}
