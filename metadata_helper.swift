import Foundation
import ImageIO
import AVFoundation

let args=CommandLine.arguments
guard args.count>=4,args[1]=="--type" else{exit(2)}
let type=args[2],path=args[3],url=URL(fileURLWithPath:path)
var result:[String:String]=["path":path]
let outputDate=DateFormatter();outputDate.dateFormat="yyyy-MM-dd"

if type=="PHOTO" {
    if let source=CGImageSourceCreateWithURL(url as CFURL,[kCGImageSourceShouldCache:false] as CFDictionary),let props=CGImageSourceCopyPropertiesAtIndex(source,0,[kCGImageSourceShouldCache:false] as CFDictionary) as? [String:Any] {
        if let tiff=props[kCGImagePropertyTIFFDictionary as String] as? [String:Any] {
            let make=(tiff[kCGImagePropertyTIFFMake as String] as? String)?.trimmingCharacters(in:.whitespaces) ?? ""
            let model=(tiff[kCGImagePropertyTIFFModel as String] as? String)?.trimmingCharacters(in:.whitespaces) ?? ""
            if !model.isEmpty{result["device"]=model.lowercased().hasPrefix(make.lowercased()) ? model:[make,model].filter{!$0.isEmpty}.joined(separator:" ")}
        }
        if let exif=props[kCGImagePropertyExifDictionary as String] as? [String:Any],let raw=(exif[kCGImagePropertyExifDateTimeOriginal as String] ?? exif[kCGImagePropertyExifDateTimeDigitized as String]) as? String {
            let f=DateFormatter();f.dateFormat="yyyy:MM:dd HH:mm:ss";if let d=f.date(from:raw){result["date"]=outputDate.string(from:d);result["timestamp"]=String(d.timeIntervalSince1970)}
        }
        if let g=props[kCGImagePropertyGPSDictionary as String] as? [String:Any],let a=g[kCGImagePropertyGPSLatitude as String] as? NSNumber,let o=g[kCGImagePropertyGPSLongitude as String] as? NSNumber {
            var lat=a.doubleValue,lon=o.doubleValue;if (g[kCGImagePropertyGPSLatitudeRef as String] as? String)=="S"{lat = -lat};if (g[kCGImagePropertyGPSLongitudeRef as String] as? String)=="W"{lon = -lon};result["latitude"]=String(lat);result["longitude"]=String(lon)
        }
    }
} else if type=="VIDEO" {
    let asset=AVURLAsset(url:url)
    if let item=asset.commonMetadata.first(where:{$0.commonKey?.rawValue=="creationDate"}),let raw=item.stringValue,let d=ISO8601DateFormatter().date(from:raw){result["date"]=outputDate.string(from:d);result["timestamp"]=String(d.timeIntervalSince1970)}
    for item in asset.metadata where item.identifier?.rawValue.lowercased().contains("model")==true {if let value=item.stringValue,!value.isEmpty{result["device"]=value;break}}
}
let n=url.lastPathComponent.lowercased();if n.contains("timelapse")||n.contains("time-lapse")||n.contains("time_lapse")||n.contains("延时"){result["timelapse"]="true"}
let data=try JSONSerialization.data(withJSONObject:result);FileHandle.standardOutput.write(data)
