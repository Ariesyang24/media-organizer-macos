import SwiftUI
import AppKit
import CoreLocation
import CryptoKit
import Darwin
import UniformTypeIdentifiers

enum LocationSource:String {
    case folderName = "folder_name", gps = "gps", manual = "manual", unknown = "unknown"
    var label:String { switch self { case .folderName:return "文件夹";case .gps:return "GPS";case .manual:return "手动";case .unknown:return "未设置" } }
}

struct MediaRecord: Identifiable {
    let id = UUID(); let source: URL
    var date:String;var captureTimestamp:Double;var location:String;var locationSource:LocationSource
    var gpsLocation:String?;var gpsLatitude:Double?;var gpsLongitude:Double?;var device:String;var timelapse:Bool;var kind:String
    var originalFolderName:String?;var inheritedFolderPath:String?;var inheritedLocation:String?;var structureRootPath:String?;var collectionKey:String?;var collectionFolder:String?;var outputFileName:String?=nil;var batch="";var target=""
}

struct MetaResult {
    var date: String; var location = "未知地区"; var device: String; var timelapse: Bool
    var timestamp: Double; var latitude: Double?; var longitude: Double?
}

struct ScanFailure { let path: String; let stage: String; let reason: String }

enum WorkPhase:String { case idle,enumerating,metadata,location,preview,organizing,completed,cancelled,failed }
enum NamingLanguage:String,CaseIterable,Identifiable {case chinese="中文",english="English";var id:String{rawValue}}
enum InterfaceLanguage:String,CaseIterable,Identifiable {case chinese="中文",english="English";var id:String{rawValue}}

final class ScanLogger {
    let url: URL; private let queue = DispatchQueue(label: "scan.logger")
    private let formatter = ISO8601DateFormatter()
    private var handle: FileHandle?
    init() {
        let dir = ProcessInfo.processInfo.environment["MATERIAL_LOG_DIR"].map{URL(fileURLWithPath:$0)} ?? FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Library/Logs/Media Organizer")
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        let f = DateFormatter(); f.dateFormat = "yyyyMMdd-HHmmss"
        url = dir.appendingPathComponent("scan-\(f.string(from: Date())).log")
        FileManager.default.createFile(atPath: url.path, contents: nil)
        handle = try? FileHandle(forWritingTo:url)
    }
    func write(_ area: String, _ message: String) {
        let line = "[\(formatter.string(from: Date()))] [\(area)] \(message)\n"
        queue.async { if let data=line.data(using:.utf8) { try? self.handle?.write(contentsOf:data) } }
    }
}

final class OrganizerModel: ObservableObject {
    @Published var sources:[URL]=[]; @Published var excludes:[URL]=[]
    @Published var output=FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Pictures/所有素材")
    @Published var records:[MediaRecord]=[]; @Published var status="请选择素材来源、成片目录和总素材文件夹"
    @Published var busy=false; @Published var copyMode=true
    @Published var phase:WorkPhase = .idle; @Published var progressDone=0; @Published var progressTotal=0
    @Published var currentFile=""; @Published var failureCount=0
    @Published var taskCompleted=false
    let photoExts=Set(["jpg","jpeg","heic","heif","png","tif","tiff","gif","webp","dng","cr2","cr3","nef","arw","raf","orf","rw2"])
    let videoExts=Set(["mov","mp4","m4v","avi","mkv","mts","m2ts","mxf","3gp"])
    @Published var selectedBatches=Set<String>();@Published var batchLocation=""
    @Published var renamePhotos=false;@Published var selectedRenameFolders=Set<String>();@Published var customPhotoName=""
    @Published var namingLanguage:NamingLanguage = .chinese
    private let stateLock=NSLock(); private var cancelled=false; private var running:[Process]=[]
    private var outputNeedsConfirmation=false

    init(){
        if let path=UserDefaults.standard.string(forKey:"LastMaterialOutputPath"){
            output=URL(fileURLWithPath:path)
            if !FileManager.default.fileExists(atPath:path){outputNeedsConfirmation=true;status="上次总素材文件夹当前不可用，执行整理前需要重新确认：\(path)"}
        }
    }

    func chooseFolders(title:String,multiple:Bool)->[URL]{let p=NSOpenPanel();p.title=title;p.canChooseDirectories=true;p.canChooseFiles=false;p.allowsMultipleSelection=multiple;return p.runModal() == .OK ? p.urls:[]}
    func addSources(){for u in chooseFolders(title:"选择素材来源",multiple:true) where !sources.contains(u){sources.append(u)}}
    func removeSource(_ url:URL){sources.removeAll{$0.standardizedFileURL == url.standardizedFileURL}}
    func addDroppedSources(_ providers:[NSItemProvider])->Bool {
        let matching=providers.filter{$0.hasItemConformingToTypeIdentifier(UTType.fileURL.identifier)}
        guard !matching.isEmpty else{return false}
        for provider in matching {
            provider.loadItem(forTypeIdentifier:UTType.fileURL.identifier,options:nil){item,_ in
                var url:URL?
                if let data=item as? Data{url=URL(dataRepresentation:data,relativeTo:nil)}
                else if let value=item as? URL{url=value}
                DispatchQueue.main.async {
                    guard let url else{return};var isDirectory:ObjCBool=false
                    guard FileManager.default.fileExists(atPath:url.path,isDirectory:&isDirectory),isDirectory.boolValue else{self.status="只能拖入文件夹，已忽略：\(url.lastPathComponent)";return}
                    if !self.sources.contains(url){self.sources.append(url);self.status="已添加素材来源：\(url.path)"}
                }
            }
        }
        return true
    }
    func addExcludes(){for u in chooseFolders(title:"选择修完图或成片目录",multiple:true) where !excludes.contains(u){excludes.append(u)}}
    func removeExclude(_ url:URL){excludes.removeAll{$0.standardizedFileURL == url.standardizedFileURL}}
    func chooseOutput(){if let u=chooseFolders(title:"选择总素材文件夹",multiple:false).first{output=u;outputNeedsConfirmation=false;UserDefaults.standard.set(u.standardizedFileURL.path,forKey:"LastMaterialOutputPath")}}
    func openOutput(){NSWorkspace.shared.open(output)}
    func backToSelection(){guard !busy else{return};records=[];selectedBatches=[];batchLocation="";renamePhotos=false;selectedRenameFolders=[];customPhotoName="";progressDone=0;progressTotal=0;failureCount=0;currentFile="";taskCompleted=false;phase = .idle;status="已返回选择范围；可以增删素材来源或继续拖入文件夹"}
    func startNextTask(){guard !busy else{return};sources=[];excludes=[];records=[];selectedBatches=[];batchLocation="";renamePhotos=false;selectedRenameFolders=[];customPhotoName="";progressDone=0;progressTotal=0;failureCount=0;currentFile="";taskCompleted=false;phase = .idle;status="请选择下一批素材来源；总素材文件夹已保留"}
    func inside(_ u:URL,roots:[URL])->Bool{let p=u.standardizedFileURL.path;return roots.contains{p==$0.standardizedFileURL.path || p.hasPrefix($0.standardizedFileURL.path+"/")}}
    func isCancelled()->Bool{stateLock.lock();defer{stateLock.unlock()};return cancelled}
    func cancelScan(){stateLock.lock();cancelled=true;let tasks=running;stateLock.unlock();for p in tasks where p.isRunning{p.terminate();Darwin.kill(p.processIdentifier,SIGKILL)};status="正在安全停止……"}
    func track(_ p:Process,_ add:Bool){stateLock.lock();if add{running.append(p)}else{running.removeAll{$0===p}};stateLock.unlock()}

    func scan(){
        guard !sources.isEmpty else{status="请先添加素材来源";return}
        stateLock.lock();cancelled=false;stateLock.unlock();busy=true;records=[];taskCompleted=false;phase = .enumerating;progressDone=0;progressTotal=0;failureCount=0;currentFile="";status="正在枚举素材……"
        let sourceList=sources,excludedFolders=excludes,destination=output,started=Date(),logger=ScanLogger()
        logger.write("SCAN","BEGIN sources=\(sourceList.map(\.path).joined(separator:";"))")
        DispatchQueue.global(qos:.userInitiated).async {
            var finalRecords:[MediaRecord]=[];var failures:[ScanFailure]=[];var finalStatus=""
            defer { DispatchQueue.main.async { self.records=finalRecords;self.busy=false;self.failureCount=failures.count;self.phase=self.isCancelled() ? .cancelled:(finalRecords.isEmpty && !failures.isEmpty ? .failed:.completed);self.currentFile="";self.status=finalStatus+"；日志：\(logger.url.path)" } }
            let access=(sourceList+excludedFolders+[destination]).map{($0,$0.startAccessingSecurityScopedResource())}
            defer{for(u,ok) in access where ok{u.stopAccessingSecurityScopedResource()}}
            var urls:[URL]=[];let fm=FileManager.default
            for source in sourceList {
                if self.isCancelled(){break};logger.write("ENUM","DIR \(source.path)")
                var excluded=excludedFolders;if self.inside(destination,roots:[source]){excluded.append(destination)}
                let keys:[URLResourceKey]=[.isRegularFileKey,.isDirectoryKey,.isSymbolicLinkKey,.isPackageKey,.isUbiquitousItemKey,.ubiquitousItemDownloadingStatusKey]
                guard let en=fm.enumerator(at:source,includingPropertiesForKeys:keys,options:[.skipsHiddenFiles,.skipsPackageDescendants],errorHandler:{u,e in failures.append(.init(path:u.path,stage:"ENUM",reason:e.localizedDescription));logger.write("ENUM","ERROR path=\(u.path) error=\(e.localizedDescription)");return true})else{continue}
                while let u=en.nextObject() as? URL {
                    if self.isCancelled(){break}
                    if self.inside(u,roots:excluded){en.skipDescendants();continue}
                    let v=try? u.resourceValues(forKeys:Set(keys))
                    if v?.isSymbolicLink==true || v?.isPackage==true{en.skipDescendants();continue}
                    guard v?.isRegularFile==true else{continue}
                    if v?.isUbiquitousItem==true && v?.ubiquitousItemDownloadingStatus != .current { failures.append(.init(path:u.path,stage:"ICLOUD",reason:"文件尚未下载"));logger.write("SCAN","SKIP path=\(u.path) reason=iCloud-not-downloaded");continue }
                    let ext=u.pathExtension.lowercased();if self.photoExts.contains(ext)||self.videoExts.contains(ext){urls.append(u)}
                }
            }
            logger.write("ENUM","DONE files=\(urls.count) elapsed=\(String(format:"%.2f",Date().timeIntervalSince(started)))s")
            if self.isCancelled(){finalStatus="已取消：发现 \(urls.count) 个文件";logger.write("SCAN","CANCELLED stage=enumeration");return}
            DispatchQueue.main.async{self.phase = .metadata;self.progressTotal=urls.count;self.progressDone=0;self.status="已发现 \(urls.count) 个文件，正在安全读取元数据……"}
            let lock=NSLock();let metadataSlots=DispatchSemaphore(value:4);var metas=Array<MetaResult?>(repeating:nil,count:urls.count);var done=0
            DispatchQueue.concurrentPerform(iterations:urls.count){i in
                if self.isCancelled(){return};metadataSlots.wait();defer{metadataSlots.signal()};if self.isCancelled(){return};let u=urls[i],t=Date(),kind=self.photoExts.contains(u.pathExtension.lowercased()) ? "PHOTO":"VIDEO"
                logger.write("SCAN","\(i+1)/\(urls.count) START type=\(kind) path=\(u.path)");logger.write("META","START path=\(u.path)")
                let result=self.readMetadata(u,type:kind,timeout:10,logger:logger)
                lock.lock();if let m=result.meta{metas[i]=m}else{failures.append(.init(path:u.path,stage:"META",reason:result.error ?? "未知错误"))};done+=1;let n=done;lock.unlock()
                logger.write("THUMB","SKIP path=\(u.path) reason=not-implemented");logger.write("SCAN","\(i+1)/\(urls.count) \(result.meta == nil ? "SKIP":"DONE") elapsed=\(String(format:"%.2f",Date().timeIntervalSince(t)))s")
                if n%10==0 || n==urls.count{DispatchQueue.main.async{self.progressDone=n;self.currentFile=u.lastPathComponent;self.status="正在读取 \(n)/\(urls.count)：\(u.lastPathComponent)"}}
            }
            if self.isCancelled(){finalStatus="已取消：完成 \(done)/\(urls.count)";logger.write("SCAN","CANCELLED processed=\(done) total=\(urls.count)");return}
            DispatchQueue.main.async{self.phase = .location;self.status="正在解析地点信息……"};self.resolveLocations(&metas, logger:logger)
            for i in urls.indices {
                guard let m=metas[i] else{continue};let u=urls[i]
                let root=sourceList.first(where:{self.inside(u,roots:[$0])}) ?? u.deletingLastPathComponent()
                let event=self.folderEvent(for:u,sourceRoot:root)
                let inherited=event.map{(label:$0.location,path:$0.path)} ?? self.folderLocation(for:u,sourceRoot:root)
                let gps=m.location == "未知地区" ? nil:m.location
                let resolved=self.initialLocation(folder:inherited?.label,gps:gps)
                let location=resolved.0;let source=resolved.1
                let collectionEvent=self.collectionEvent(for:u,sourceRoot:root)
                let collection=collectionEvent.map{"\(self.displayDate($0.date)) \($0.location)"}
                finalRecords.append(MediaRecord(source:u,date:event?.date ?? m.date,captureTimestamp:m.timestamp,location:location,locationSource:source,gpsLocation:gps,gpsLatitude:m.latitude,gpsLongitude:m.longitude,device:m.device,timelapse:false,kind:self.photoExts.contains(u.pathExtension.lowercased()) ? "照片":"视频",originalFolderName:u.deletingLastPathComponent().lastPathComponent,inheritedFolderPath:inherited?.path,inheritedLocation:inherited?.label,structureRootPath:event?.path ?? root.standardizedFileURL.path,collectionKey:collectionEvent?.path,collectionFolder:collection))
            }
            self.detectSequences(&finalRecords);self.assignTargets(&finalRecords)
            DispatchQueue.main.async{self.phase = .preview};finalStatus="扫描完成：成功 \(finalRecords.count)，失败/跳过 \(failures.count)"
            logger.write("SCAN","COMPLETE success=\(finalRecords.count) failed=\(failures.count) elapsed=\(String(format:"%.2f",Date().timeIntervalSince(started)))s")
            for f in failures{logger.write("FAIL","stage=\(f.stage) path=\(f.path) error=\(f.reason)")}
        }
    }

    func fallback(_ u:URL)->MetaResult{let d=(try? u.resourceValues(forKeys:[.contentModificationDateKey]).contentModificationDate) ?? Date();let n=u.lastPathComponent.lowercased();return .init(date:day(d),device:"未知设备",timelapse:n.contains("timelapse")||n.contains("time-lapse")||n.contains("延时"),timestamp:d.timeIntervalSince1970)}
    func readMetadata(_ u:URL,type:String,timeout:TimeInterval,logger:ScanLogger)->(meta:MetaResult?,error:String?){
        return autoreleasepool {
        let helper=ProcessInfo.processInfo.environment["MATERIAL_HELPER_PATH"].map{URL(fileURLWithPath:$0)} ?? Bundle.main.bundleURL.deletingLastPathComponent().appendingPathComponent("metadata_helper");guard FileManager.default.isExecutableFile(atPath:helper.path)else{return(fallback(u),"辅助组件不可用")}
        let p=Process(),out=Pipe(),err=Pipe();p.executableURL=helper;p.arguments=["--type",type,u.path];p.standardOutput=out;p.standardError=err
        defer{try?out.fileHandleForReading.close();try?err.fileHandleForReading.close();try?out.fileHandleForWriting.close();try?err.fileHandleForWriting.close()}
        do{try p.run();try?out.fileHandleForWriting.close();try?err.fileHandleForWriting.close();track(p,true);let deadline=Date().addingTimeInterval(timeout);while p.isRunning && Date()<deadline && !isCancelled(){Thread.sleep(forTimeInterval:0.05)};if p.isRunning{logger.write("META","TIMEOUT path=\(u.path) limit=\(timeout)s");p.terminate();Thread.sleep(forTimeInterval:0.1);if p.isRunning{Darwin.kill(p.processIdentifier,SIGKILL)}};p.waitUntilExit();track(p,false)
            if isCancelled(){return(nil,"用户取消")};if Date()>=deadline{return(nil,"metadata 超时")}
            let data=out.fileHandleForReading.readDataToEndOfFile();let errorText=String(data:err.fileHandleForReading.readDataToEndOfFile(),encoding:.utf8) ?? ""
            guard let x=try? JSONSerialization.jsonObject(with:data) as? [String:String]else{logger.write("META","FAILED path=\(u.path) error=\(errorText)");return(nil,"元数据读取失败")}
            var m=fallback(u);m.date=x["date"] ?? m.date;m.device=x["device"] ?? m.device;m.timestamp=Double(x["timestamp"] ?? "") ?? m.timestamp;m.timelapse=x["timelapse"]=="true" || m.timelapse;m.latitude=Double(x["latitude"] ?? "");m.longitude=Double(x["longitude"] ?? "")
            logger.write("META","DONE path=\(u.path)");return(m,nil)
        }catch{track(p,false);logger.write("META","FAILED path=\(u.path) error=\(error.localizedDescription)");return(nil,error.localizedDescription)}
        }
    }
    func day(_ d:Date)->String{let f=DateFormatter();f.dateFormat="yyyy-MM-dd";return f.string(from:d)}
    func folderEvent(for file:URL,sourceRoot:URL)->(date:String,location:String,path:String)? {
        var dir=file.deletingLastPathComponent();var candidates:[URL]=[]
        while inside(dir,roots:[sourceRoot]) {
            candidates.append(dir)
            if dir.standardizedFileURL==sourceRoot.standardizedFileURL{break}
            let parent=dir.deletingLastPathComponent();if parent==dir{break};dir=parent
        }
        // 从最近的目录开始：内层再出现明确日期＋地点时，开启新事件。
        for candidate in candidates {
            if let parsed=parseEventFolder(candidate.lastPathComponent){return(parsed.date,parsed.location,candidate.path)}
        }
        return nil
    }
    func collectionEvent(for file:URL,sourceRoot:URL)->(date:String,location:String,path:String)? {
        // 来源本身是项目目录时直接使用；来源是“照片素材”等容器时，把其一级子目录分别当作独立项目。
        if let parsed=parseEventFolder(sourceRoot.lastPathComponent){return(parsed.date,parsed.location,sourceRoot.standardizedFileURL.path)}
        let rootPath=sourceRoot.standardizedFileURL.path,filePath=file.standardizedFileURL.path
        guard filePath.hasPrefix(rootPath+"/") else{return nil}
        let relative=String(filePath.dropFirst(rootPath.count+1))
        guard let first=relative.split(separator:"/").first else{return nil}
        let child=sourceRoot.appendingPathComponent(String(first),isDirectory:true)
        guard let parsed=parseEventFolder(child.lastPathComponent) else{return nil}
        return(parsed.date,parsed.location,child.standardizedFileURL.path)
    }
    func parseEventFolder(_ original:String)->(date:String,location:String)? {
        let text=original.trimmingCharacters(in:.whitespacesAndNewlines)
        let pattern="(?<!\\d)(20\\d{2})[.\\-_年](\\d{1,2})[.\\-_月](\\d{1,2})日?"
        guard let regex=try?NSRegularExpression(pattern:pattern),let match=regex.firstMatch(in:text,range:NSRange(text.startIndex...,in:text)),let full=Range(match.range(at:0),in:text),let yr=Range(match.range(at:1),in:text),let mo=Range(match.range(at:2),in:text),let dy=Range(match.range(at:3),in:text),let month=Int(text[mo]),let day=Int(text[dy])else{return nil}
        let date=String(format:"%@-%02d-%02d",String(text[yr]),month,day)
        var rest=text.replacingCharacters(in:full,with:"")
        rest=rest.replacingOccurrences(of:"^[\\s._-]+|[\\s._-]+$",with:"",options:.regularExpression)
        guard let location=parseFolderLocation(rest),!location.isEmpty else{return nil}
        return(date,location)
    }
    func folderLocation(for file:URL,sourceRoot:URL)->(label:String,path:String)? {
        var dir=file.deletingLastPathComponent();var checked=0
        while checked<3 && inside(dir,roots:[sourceRoot]) {
            if let label=parseFolderLocation(dir.lastPathComponent){return(label,dir.path)}
            if dir.standardizedFileURL==sourceRoot.standardizedFileURL{break};dir=dir.deletingLastPathComponent();checked+=1
        }
        return nil
    }
    func initialLocation(folder:String?,gps:String?)->(String,LocationSource){if let folder,!folder.isEmpty{return(folder,.folderName)};if let gps,!gps.isEmpty{return(gps,.gps)};return("未设置",.unknown)}
    func parseFolderLocation(_ original:String)->String? {
        let trimmed=original.trimmingCharacters(in:.whitespacesAndNewlines);if trimmed.isEmpty{return nil}
        let lower=trimmed.lowercased()
        let compact=lower.replacingOccurrences(of:"[ _-]",with:"",options:.regularExpression)
        if ["sony","canon","nikon","panasonic","dji","gopro","insta360","s1r2","s1rii"].contains(compact){return nil}
        let generic=Set(["dcim","private","photo","photos","video","videos","照片","视频","素材","照片素材","摄影素材","拍摄素材","所有素材","原片","精修","导出","成片","raw","jpg","jpeg","mov","mp4","日出","日落","夜景","秋季","无人机"])
        if generic.contains(lower){return nil}
        if lower.range(of:"^\\d{4}$",options:.regularExpression) != nil || lower.range(of:"^\\d{4}[-._年]\\d{1,2}([-.月_]\\d{1,2}日?)?$",options:.regularExpression) != nil{return nil}
        if lower.range(of:"^\\d{3}[_-]?(pana|canon|nikon|sony|dji)?$",options:.regularExpression) != nil{return nil}
        var value=trimmed
        let patterns=["(?i)^\\d{4}[-.]\\d{1,2}[-.]\\d{1,2}[ _.-]*","(?i)(^|[_ ]+)(s1r2|s1rii|sony|canon|nikon|panasonic|dji|gopro|insta360|raw|jpe?g|mov|mp4|video|photo|照片|视频|素材|原片|精修|导出|成片)([_ ]+|$)"]
        for pattern in patterns{value=value.replacingOccurrences(of:pattern,with:"_",options:.regularExpression)}
        value=value.replacingOccurrences(of:"[_ ]+",with:" ",options:.regularExpression).trimmingCharacters(in:CharacterSet.whitespacesAndNewlines.union(CharacterSet(charactersIn:"_-")));let changed=value != trimmed
        if value.isEmpty || generic.contains(value.lowercased()){return nil}
        let meaningful=value.range(of:"[\\p{Han}]",options:.regularExpression) != nil || value.filter{$0.isLetter}.count>=3
        return meaningful ? value:(changed ? nil:trimmed)
    }
    func resolveLocations(_ metas:inout[MetaResult?],logger:ScanLogger){
        var cache:[String:String]=[:];var failed=Set<String>()
        for i in metas.indices {
            if isCancelled(){return};guard let lat=metas[i]?.latitude,let lon=metas[i]?.longitude else{continue}
            let key=String(format:"%.1f,%.1f",lat,lon)
            if let known=cache[key]{metas[i]?.location=known;logger.write("GPS","CACHE_HIT key=\(key)");continue}
            if failed.contains(key){logger.write("GPS","CACHE_HIT_FAILED key=\(key)");continue}
            DispatchQueue.main.async{self.status="正在识别地区 \(key)……"};logger.write("GPS","START key=\(key)")
            let sem=DispatchSemaphore(value:0);var place:String?
            CLGeocoder().reverseGeocodeLocation(CLLocation(latitude:lat,longitude:lon),preferredLocale:Locale(identifier:"zh_CN")){marks,error in
                if let p=marks?.first{place=p.locality ?? p.subAdministrativeArea ?? p.administrativeArea ?? p.country}
                if let error{logger.write("GPS","FAILED key=\(key) error=\(error.localizedDescription)")};sem.signal()
            }
            let ok=sem.wait(timeout:.now()+3) == .success
            if let place{cache[key]=place;metas[i]?.location=place;logger.write("GPS","DONE key=\(key) result=\(place)")}else{failed.insert(key);if !ok{logger.write("GPS","TIMEOUT key=\(key) limit=3s")}}
        }
    }
    func detectSequences(_ v:inout[MediaRecord]){
        // 延时判断以原始文件夹为单位，分别抽查开头、中间、结尾；三段都规律且间隔一致才通过。
        var photoIndicesByFolder:[String:[Int]]=[:]
        for i in v.indices where v[i].kind == "照片" {
            let folder=v[i].source.deletingLastPathComponent().standardizedFileURL.path
            photoIndicesByFolder[folder,default:[]].append(i)
        }
        for (_,indices) in photoIndicesByFolder {
            let ordered=indices.sorted{v[$0].captureTimestamp < v[$1].captureTimestamp}
            guard ordered.count >= 18 else{continue}
            let sampleCount=min(8,ordered.count/3)
            let middleStart=max(0,(ordered.count-sampleCount)/2)
            let ranges=[0..<sampleCount,middleStart..<(middleStart+sampleCount),(ordered.count-sampleCount)..<ordered.count]
            var representativeIntervals:[Double]=[];var allSegmentsValid=true
            for range in ranges {
                let times=range.map{v[ordered[$0]].captureTimestamp}
                let gaps=(1..<times.count).map{times[$0]-times[$0-1]}.sorted()
                guard !gaps.isEmpty else{allSegmentsValid=false;break}
                let interval=gaps[gaps.count/2],tolerance=max(0.35,interval*0.05)
                guard interval >= 1.0 && interval <= 30.0,
                      gaps.allSatisfy({$0 >= 1.0 && $0 <= 30.0 && abs($0-interval) <= tolerance})
                else{allSegmentsValid=false;break}
                representativeIntervals.append(interval)
            }
            if allSegmentsValid,representativeIntervals.count == 3 {
                let reference=representativeIntervals.sorted()[1],crossTolerance=max(0.35,reference*0.05)
                if representativeIntervals.allSatisfy({abs($0-reference) <= crossTolerance}) {
                    for index in indices { v[index].timelapse=true }
                }
            }
        }
    }
    func safe(_ s:String)->String{let bad=CharacterSet(charactersIn:"/:*?\"<>|\\\n\r");let x=s.components(separatedBy:bad).joined(separator:"-");return x.trimmingCharacters(in:.whitespacesAndNewlines).isEmpty ? "未知":x}
    func englishPathComponent(_ source:String)->String {
        let fixed:[String:String]=["未设置":"Unknown Location","未知地区":"Unknown Location","未知设备":"Unknown Device","照片":"Photos","视频":"Videos"]
        if let value=fixed[source]{return value}
        let value=NSMutableString(string:source)
        CFStringTransform(value,nil,kCFStringTransformToLatin,false)
        CFStringTransform(value,nil,kCFStringTransformStripCombiningMarks,false)
        var result=(value as String).replacingOccurrences(of:"[^A-Za-z0-9._ -]+",with:"-",options:.regularExpression)
        result=result.replacingOccurrences(of:"[ _-]+",with:" ",options:.regularExpression).trimmingCharacters(in:.whitespacesAndNewlines)
        return result.isEmpty ? "Unknown":result
    }
    func pathComponent(_ source:String)->String{namingLanguage == .english ? englishPathComponent(source):safe(source)}
    func setNamingLanguage(_ language:NamingLanguage){namingLanguage=language;refreshTargets()}
    func displayDate(_ date:String)->String{let parts=date.split(separator:"-");guard parts.count==3,let month=Int(parts[1]),let day=Int(parts[2])else{return date};return "\(parts[0]).\(month).\(day)"}
    func assignTargets(_ v:inout[MediaRecord]){
        // 同一原文件夹内的照片和视频属于同一设备；视频元数据缺失时继承照片识别出的设备。
        var knownDeviceByFolder:[String:String]=[:]
        for record in v {
            let folder=record.source.deletingLastPathComponent().standardizedFileURL.path
            if record.device != "未知设备" && !record.device.isEmpty { knownDeviceByFolder[folder]=record.device }
        }
        for i in v.indices {
            let folder=v[i].source.deletingLastPathComponent().standardizedFileURL.path
            if (v[i].device == "未知设备" || v[i].device.isEmpty),let inherited=knownDeviceByFolder[folder] { v[i].device=inherited }
        }
        var foldersByGroup:[String:Set<String>]=[:]
        for i in v.indices {
            let place=safe(v[i].location);v[i].batch="\(displayDate(v[i].date)) \(place)"
            let eventFolder="\(displayDate(v[i].date)) \(pathComponent(v[i].location))"
            let pathBatch=v[i].collectionFolder.map{pathComponent($0)}.flatMap{$0 == eventFolder ? nil:"\($0)/\(eventFolder)"} ?? eventFolder
            let pathDevice=pathComponent(v[i].device)
            let parent=v[i].source.deletingLastPathComponent().standardizedFileURL.path
            let root=v[i].structureRootPath.map{URL(fileURLWithPath:$0).standardizedFileURL.path}
            if let root,parent.hasPrefix(root+"/") { foldersByGroup["\(pathBatch)/\(pathDevice)",default:[]].insert(parent) }
        }
        var folderNumbers:[String:[String:String]]=[:]
        for (group,folders) in foldersByGroup {
            guard folders.count > 1 else{continue}
            for (offset,folder) in folders.sorted().enumerated() { folderNumbers[group,default:[:]][folder]=String(format:"%03d",offset+1) }
        }
        for i in v.indices {
            let eventFolder="\(displayDate(v[i].date)) \(pathComponent(v[i].location))"
            let pathBatch=v[i].collectionFolder.map{pathComponent($0)}.flatMap{$0 == eventFolder ? nil:"\($0)/\(eventFolder)"} ?? eventFolder
            let pathDevice=pathComponent(v[i].device)
            let numberingGroup="\(pathBatch)/\(pathDevice)"
            let typeName=namingLanguage == .english ? (v[i].kind == "照片" ? "Photos":"Videos"):v[i].kind
            let targetGroup="\(pathBatch)/\(pathDevice) \(typeName)"
            let parent=v[i].source.deletingLastPathComponent().standardizedFileURL.path
            let timelapseSuffix=namingLanguage == .english ? " Timelapse":" 延时"
            v[i].target=folderNumbers[numberingGroup]?[parent].map{"\(targetGroup)/\($0)\(v[i].timelapse && v[i].kind == "照片" ? timelapseSuffix:"")"} ?? targetGroup
        }
    }
    func refreshTargets(){var c=records;assignTargets(&c);records=c}
    var batchNames:[String]{Array(Set(records.map(\.batch).filter{!$0.isEmpty})).sorted()}
    func toggleBatch(_ batch:String){if selectedBatches.contains(batch){selectedBatches.remove(batch)}else{selectedBatches.insert(batch)}}
    func applyBatchLocation(){let value=batchLocation.trimmingCharacters(in:.whitespacesAndNewlines);guard !selectedBatches.isEmpty,!value.isEmpty else{return};for i in records.indices where selectedBatches.contains(records[i].batch){records[i].location=value;records[i].locationSource = .manual};refreshTargets()}
    func clearBatchLocation(){guard !selectedBatches.isEmpty else{return};for i in records.indices where selectedBatches.contains(records[i].batch){if let folder=records[i].inheritedLocation{records[i].location=folder;records[i].locationSource = .folderName}else if let gps=records[i].gpsLocation{records[i].location=gps;records[i].locationSource = .gps}else{records[i].location="未设置";records[i].locationSource = .unknown}};refreshTargets()}
    func setManualLocation(_ id:UUID,_ value:String){if let i=records.firstIndex(where:{$0.id==id}){records[i].location=value;records[i].locationSource=value.trimmingCharacters(in:.whitespacesAndNewlines).isEmpty ? .unknown:.manual;refreshTargets()}}
    func setDevice(_ id:UUID,_ value:String){if let i=records.firstIndex(where:{$0.id==id}){records[i].device=value;refreshTargets()}}
    func setTimelapse(_ id:UUID,_ value:Bool){if let i=records.firstIndex(where:{$0.id==id}){records[i].timelapse=value;refreshTargets()}}
    var collectionItems:[(key:String,name:String)]{
        var result:[String:String]=[:];for record in records{if let key=record.collectionKey,let name=record.collectionFolder{result[key]=name}}
        return result.map{($0.key,$0.value)}.sorted{$0.name<$1.name}
    }
    func setCollectionName(_ key:String,_ value:String){for i in records.indices where records[i].collectionKey==key{records[i].collectionFolder=value};refreshTargets()}
    var photoTargetFolders:[String]{Array(Set(records.filter{$0.kind=="照片"}.map(\.target))).sorted()}
    func setRenamePhotos(_ enabled:Bool){renamePhotos=enabled;if !enabled{selectedRenameFolders=[];customPhotoName="";for i in records.indices{records[i].outputFileName=nil}}}
    func toggleRenameFolder(_ folder:String){if selectedRenameFolders.contains(folder){selectedRenameFolders.remove(folder)}else{selectedRenameFolders.insert(folder)}}
    func applyPhotoRename(){
        let base=safe(customPhotoName).trimmingCharacters(in:.whitespacesAndNewlines)
        guard renamePhotos,!base.isEmpty,!selectedRenameFolders.isEmpty else{return}
        for folder in selectedRenameFolders {
            let indices=records.indices.filter{records[$0].kind=="照片" && records[$0].target==folder}
            var stems:[String:(time:Double,indices:[Int])]=[:]
            for index in indices {let stem=records[index].source.deletingPathExtension().lastPathComponent;let current=stems[stem];stems[stem]=(min(current?.time ?? records[index].captureTimestamp,records[index].captureTimestamp),(current?.indices ?? [])+[index])}
            for (offset,item) in stems.sorted(by:{$0.value.time == $1.value.time ? $0.key < $1.key:$0.value.time < $1.value.time}).enumerated(){
                for index in item.value.indices {records[index].outputFileName="\(base)_\(String(format:"%04d",offset+1)).\(records[index].source.pathExtension.lowercased())"}
            }
        }
        status="已为所选 \(selectedRenameFolders.count) 个照片文件夹生成自定义文件名预览"
    }
    func csv(_ s:String)->String{"\""+s.replacingOccurrences(of:"\"",with:"\"\"")+"\""}
    func sha256(_ url:URL)throws->String{
        let handle=try FileHandle(forReadingFrom:url);defer{try?handle.close()};var hash=SHA256()
        while true {
            var reachedEnd=false
            try autoreleasepool {
                let data=try handle.read(upToCount:1024*1024) ?? Data()
                if data.isEmpty{reachedEnd=true}else{hash.update(data:data)}
            }
            if reachedEnd{break};if isCancelled(){throw CancellationError()}
        }
        return hash.finalize().map{String(format:"%02x",$0)}.joined()
    }
    func verifiedCopy(from source:URL,to destination:URL,sourceHash:String,fileManager fm:FileManager)throws{
        if fm.fileExists(atPath:destination.path),try sha256(destination)==sourceHash{return}
        var lastError:Error?
        for attempt in 1...3 {
            if isCancelled(){throw CancellationError()}
            let temporary=destination.deletingLastPathComponent().appendingPathComponent(".\(destination.lastPathComponent).partial-\(UUID().uuidString)")
            do{
                try fm.copyItem(at:source,to:temporary)
                guard try sha256(temporary)==sourceHash else{throw NSError(domain:"MaterialOrganizer",code:2,userInfo:[NSLocalizedDescriptionKey:"SHA-256 校验不一致（第 \(attempt) 次）"])}
                if fm.fileExists(atPath:destination.path){try fm.removeItem(at:temporary);return}
                try fm.moveItem(at:temporary,to:destination)
                return
            }catch{lastError=error;try?fm.removeItem(at:temporary)}
        }
        throw lastError ?? NSError(domain:"MaterialOrganizer",code:3,userInfo:[NSLocalizedDescriptionKey:"复制校验失败"])
    }
    func execute(){
        guard !records.isEmpty else{status="请先扫描";return}
        if outputNeedsConfirmation || !FileManager.default.fileExists(atPath:output.path){
            let warning=NSAlert();warning.messageText="请确认总素材文件夹";warning.informativeText="上次保存位置当前不可用：\n\(output.path)\n\n请选择本次实际保存位置后再执行。";warning.addButton(withTitle:"选择位置…");warning.addButton(withTitle:"取消")
            guard warning.runModal() == .alertFirstButtonReturn,let selected=chooseFolders(title:"确认总素材文件夹",multiple:false).first else{status="已取消：尚未确认总素材文件夹";return}
            output=selected;outputNeedsConfirmation=false;UserDefaults.standard.set(selected.standardizedFileURL.path,forKey:"LastMaterialOutputPath")
        }
        let list=records,out=output,copy=copyMode,fm=FileManager.default
        let required=list.reduce(Int64(0)){sum,r in sum + Int64((try? r.source.resourceValues(forKeys:[.fileSizeKey]).fileSize) ?? 0)}
        if copy,let free=(try? out.resourceValues(forKeys:[.volumeAvailableCapacityForImportantUsageKey]).volumeAvailableCapacityForImportantUsage),free < required {
            status="空间不足：预计需要 \(ByteCountFormatter.string(fromByteCount:required,countStyle:.file))，可用 \(ByteCountFormatter.string(fromByteCount:free,countStyle:.file))";return
        }
        let a=NSAlert();a.messageText="确认整理 \(list.count) 个文件？";a.informativeText="目标：\(out.path)\n方式：\(copy ? "复制并保留原文件（推荐）":"移动原文件（有风险）")\n预计数据量：\(ByteCountFormatter.string(fromByteCount:required,countStyle:.file))";a.addButton(withTitle:"执行");a.addButton(withTitle:"取消");guard a.runModal() == .alertFirstButtonReturn else{return}
        stateLock.lock();cancelled=false;stateLock.unlock();busy=true;phase = .organizing;progressDone=0;progressTotal=list.count;failureCount=0;status="正在整理 0/\(list.count)……"
        DispatchQueue.global(qos:.userInitiated).async{
            try?fm.createDirectory(at:out,withIntermediateDirectories:true);var ok=0,failed:[String]=[],completed:[(MediaRecord,String)]=[]
            for (index,r) in list.enumerated(){
                if self.isCancelled(){break}
                let dir=out.appendingPathComponent(r.target);do{try fm.createDirectory(at:dir,withIntermediateDirectories:true)}catch{failed.append("\(r.source.path): 无法创建目标目录：\(error.localizedDescription)");continue}
                do{
                    let hash=try self.sha256(r.source)
                    let plannedName=r.outputFileName ?? r.source.lastPathComponent
                    var dest=dir.appendingPathComponent(plannedName),n=2
                    while fm.fileExists(atPath:dest.path){
                        if copy,(try?self.sha256(dest))==hash{break}
                        let plannedURL=URL(fileURLWithPath:plannedName);dest=dir.appendingPathComponent("\(plannedURL.deletingPathExtension().lastPathComponent)_\(n).\(plannedURL.pathExtension)");n+=1
                    }
                    if copy{DispatchQueue.main.async{self.status="正在复制并校验 \(index+1)/\(list.count)：\(r.source.lastPathComponent)"};try self.verifiedCopy(from:r.source,to:dest,sourceHash:hash,fileManager:fm)}
                    else{try fm.moveItem(at:r.source,to:dest)}
                    ok+=1;completed.append((r,hash))
                }catch{failed.append("\(r.source.path): \(error.localizedDescription)")}
                DispatchQueue.main.async{self.progressDone=index+1;self.currentFile=r.source.lastPathComponent;self.failureCount=failed.count;self.status="正在整理 \(index+1)/\(list.count)：\(r.source.lastPathComponent)"}
            }
            let f=DateFormatter();f.dateFormat="yyyyMMdd_HHmmss";let stamp=f.string(from:Date()),csvURL=out.appendingPathComponent("整理记录_\(stamp).csv"),failURL=out.appendingPathComponent("整理失败_\(stamp).txt")
            let header="FileName,OutputFileName,OriginalPath,CaptureDate,Batch,Device,Location,LocationSource,TargetPath,SHA256,Verification\n";let rows=completed.map{item in let r=item.0;return [r.source.lastPathComponent,r.outputFileName ?? r.source.lastPathComponent,r.source.path,Date(timeIntervalSince1970:r.captureTimestamp).formatted(.iso8601),r.batch,r.device,r.location,r.locationSource.rawValue,r.target,item.1,"verified"].map(self.csv).joined(separator:",")}.joined(separator:"\n");try?(header+rows+"\n").write(to:csvURL,atomically:true,encoding:.utf8);if !failed.isEmpty{try?failed.joined(separator:"\n").write(to:failURL,atomically:true,encoding:.utf8)}
            let cancelled=self.isCancelled();DispatchQueue.main.async{self.busy=false;self.currentFile="";self.taskCompleted = !cancelled;self.phase=cancelled ? .cancelled:.completed;self.status=cancelled ? "已安全停止：完成 \(ok)/\(list.count)，原始文件未继续处理":"整理完成：成功 \(ok)，失败 \(failed.count)；记录：\(csvURL.path)"}
        }
    }
}

#if !TESTING
struct ContentView:View {
    @StateObject var model=OrganizerModel()
    @State private var dropActive=false
    @AppStorage("MediaOrganizerInterfaceLanguage") private var interfaceLanguage:InterfaceLanguage = .chinese
    private func tr(_ zh:String,_ en:String)->String{interfaceLanguage == .chinese ? zh:en}
    private var photoCount:Int{model.records.filter{$0.kind=="照片"}.count}
    private var videoCount:Int{model.records.filter{$0.kind=="视频"}.count}
    private var step:Int{model.busy ? (model.phase == .organizing ? 3:2):(model.records.isEmpty ? 1:3)}
    var body:some View {
        VStack(spacing:0) {
            header
            Divider()
            ScrollView {
                VStack(alignment:.leading,spacing:16) {
                    workflow
                    if model.busy { statusPanel }
                    if model.records.isEmpty { setupPanel } else { previewPanel }
                    if !model.busy { statusPanel }
                }.padding(20)
            }
        }.frame(minWidth:1080,minHeight:720)
    }

    private var header:some View {
        HStack(spacing:14) {
            Image(systemName:"photo.on.rectangle.angled").font(.system(size:26)).foregroundStyle(.tint)
            VStack(alignment:.leading,spacing:2){Text("Media Organizer").font(.title2.bold());Text(tr("按日期地点、设备和素材类型安全分类","Safely organize by date, location, device and media type")).font(.caption).foregroundStyle(.secondary)}
            Spacer()
            Picker("",selection:$interfaceLanguage){ForEach(InterfaceLanguage.allCases){Text($0.rawValue).tag($0)}}.pickerStyle(.segmented).frame(width:150)
            if model.busy { Button(tr("停止任务","Stop"),role:.destructive,action:model.cancelScan) }
            else if model.taskCompleted { Button(tr("打开结果文件夹","Open Results"),action:model.openOutput);Button(tr("开始下一次","Start Next"),action:model.startNextTask).buttonStyle(.borderedProminent) }
            else if model.records.isEmpty { Button(tr("扫描并预览","Scan & Preview"),action:model.scan).buttonStyle(.borderedProminent).disabled(model.sources.isEmpty) }
            else { Button(tr("返回选择","Back"),action:model.backToSelection);Button(tr("重新扫描","Rescan"),action:model.scan);Button(tr("执行整理","Organize"),action:model.execute).buttonStyle(.borderedProminent) }
        }.padding(.horizontal,20).padding(.vertical,14).background(.bar)
    }

    private var workflow:some View {
        HStack(spacing:0) {
            stepView(1,tr("选择范围","Select"),"filemenu.and.selection")
            connector(active:step>1)
            stepView(2,tr("扫描识别","Scan"),"magnifyingglass")
            connector(active:step>2)
            stepView(3,tr("预览与整理","Preview & Organize"),"square.and.arrow.down")
        }.padding(14).background(Color.secondary.opacity(0.06)).clipShape(RoundedRectangle(cornerRadius:12))
    }
    private func stepView(_ number:Int,_ title:String,_ icon:String)->some View { HStack{ZStack{Circle().fill(step>=number ? Color.accentColor:Color.secondary.opacity(0.2)).frame(width:30,height:30);if step>number{Image(systemName:"checkmark").foregroundStyle(.white)}else{Text("\(number)").foregroundStyle(step>=number ? .white:.secondary)}};Image(systemName:icon);Text(title).fontWeight(step==number ? .semibold:.regular)} }
    private func connector(active:Bool)->some View { Rectangle().fill(active ? Color.accentColor:Color.secondary.opacity(0.2)).frame(height:2).frame(maxWidth:.infinity).padding(.horizontal,14) }

    private var setupPanel:some View {
        HStack(alignment:.top,spacing:16) {
            GroupBox(tr("素材来源","Media Sources")) { VStack(alignment:.leading,spacing:10){folderList(model.sources,empty:tr("还没有素材来源","No media sources"),remove:model.removeSource);Button(tr("添加素材文件夹…","Add Media Folder…"),action:model.addSources);dropZone}.padding(8).frame(maxWidth:.infinity,alignment:.leading) }.frame(maxWidth:.infinity)
            GroupBox(tr("排除与输出","Exclusions & Output")) { VStack(alignment:.leading,spacing:10){Text(tr("成片、精修图等不参与整理","Finished exports and edited photos are excluded")).font(.caption).foregroundStyle(.secondary);folderList(model.excludes,empty:tr("未设置排除目录","No excluded folders"),remove:model.removeExclude);Button(tr("添加排除目录…","Add Excluded Folder…"),action:model.addExcludes);Divider();Picker(tr("目录命名语言","Folder Naming Language"),selection:$model.namingLanguage){ForEach(NamingLanguage.allCases){Text($0.rawValue).tag($0)}}.pickerStyle(.segmented);Text(tr("总素材文件夹","Media Library Folder")).font(.caption).foregroundStyle(.secondary);Label(model.output.path,systemImage:"externaldrive").lineLimit(2);Button(tr("更改保存位置…","Change Location…"),action:model.chooseOutput)}.padding(8).frame(maxWidth:.infinity,alignment:.leading) }.frame(maxWidth:.infinity)
        }
    }
    private var dropZone:some View { HStack{Image(systemName:"folder.badge.plus");Text(dropActive ? tr("松开以添加","Drop to add"):tr("或把素材文件夹拖到这里","Or drag media folders here"))}.frame(maxWidth:.infinity,minHeight:70).background(dropActive ? Color.accentColor.opacity(0.15):Color.secondary.opacity(0.06)).clipShape(RoundedRectangle(cornerRadius:9)).overlay(RoundedRectangle(cornerRadius:9).stroke(dropActive ? Color.accentColor:Color.secondary.opacity(0.3),style:StrokeStyle(lineWidth:1,dash:[6]))).onDrop(of:[UTType.fileURL.identifier],isTargeted:$dropActive,perform:model.addDroppedSources) }
    private func folderList(_ urls:[URL],empty:String,remove:@escaping(URL)->Void)->some View { VStack(spacing:6){if urls.isEmpty{Text(empty).foregroundStyle(.secondary).frame(maxWidth:.infinity,alignment:.leading)}else{ForEach(urls,id:\.path){u in HStack{Image(systemName:"folder.fill").foregroundStyle(.blue);Text(u.path).lineLimit(1).truncationMode(.middle);Spacer();Button{remove(u)}label:{Image(systemName:"xmark.circle.fill")}.buttonStyle(.plain).foregroundStyle(.secondary)}}}} }

    private var previewPanel:some View {
        VStack(alignment:.leading,spacing:12) {
            HStack{statCard(tr("全部","All"),model.records.count,"square.stack.3d.up");statCard(tr("照片","Photos"),photoCount,"photo");statCard(tr("视频","Videos"),videoCount,"video");statCard(tr("失败/跳过","Failed/Skipped"),model.failureCount,"exclamationmark.triangle")}
            if !model.collectionItems.isEmpty { GroupBox(tr("项目汇总文件夹命名","Project Folder Names")) { VStack(alignment:.leading,spacing:8){Text(tr("拖入总目录时，每个一级素材项目独立命名。可保留自动名称，也可逐项修改；实际路径会自动转换为所选目录语言。","Each top-level project is named independently. Keep the automatic name or edit it; paths follow the selected folder language.")).font(.caption).foregroundStyle(.secondary);ScrollView{VStack(spacing:6){ForEach(model.collectionItems,id:\.key){item in HStack{Image(systemName:"folder").foregroundStyle(.blue);Text(URL(fileURLWithPath:item.key).lastPathComponent).frame(width:240,alignment:.leading).lineLimit(1);Image(systemName:"arrow.right").foregroundStyle(.secondary);TextField(tr("项目汇总名称","Project name"),text:Binding(get:{item.name},set:{model.setCollectionName(item.key,$0)}))}}}.padding(.vertical,2)}.frame(maxHeight:150)}.padding(6) } }
            if !model.batchNames.isEmpty { GroupBox(tr("批次地点修正","Batch Location Correction")) { VStack(alignment:.leading,spacing:8){ScrollView(.horizontal){HStack{ForEach(model.batchNames,id:\.self){batch in Toggle(batch,isOn:Binding(get:{model.selectedBatches.contains(batch)},set:{_ in model.toggleBatch(batch)})).toggleStyle(.checkbox)}}};HStack{TextField(tr("为所选批次填写地点，例如：杭州西湖","Location for selected batches, e.g. West Lake Hangzhou"),text:$model.batchLocation);Button(tr("应用地点","Apply"),action:model.applyBatchLocation).disabled(model.selectedBatches.isEmpty || model.batchLocation.trimmingCharacters(in:.whitespaces).isEmpty);Button(tr("恢复自动","Restore Auto"),action:model.clearBatchLocation).disabled(model.selectedBatches.isEmpty)}}.padding(6) } }
            GroupBox(tr("照片文件重命名（可选）","Rename Photo Files (Optional)")) { VStack(alignment:.leading,spacing:8){Toggle(tr("启用照片文件重命名","Enable photo renaming"),isOn:Binding(get:{model.renamePhotos},set:model.setRenamePhotos));if model.renamePhotos{Text(tr("选择需要重命名的最末级照片文件夹；每个文件夹独立从 0001 开始。RAW＋JPG 同名配对会保持相同编号。视频不重命名。","Select final photo folders to rename. Each starts at 0001; matching RAW + JPG pairs share a number. Videos are unchanged.")).font(.caption).foregroundStyle(.secondary);ScrollView(.horizontal){HStack{ForEach(model.photoTargetFolders,id:\.self){folder in Toggle(folder,isOn:Binding(get:{model.selectedRenameFolders.contains(folder)},set:{_ in model.toggleRenameFolder(folder)})).toggleStyle(.checkbox)}}};HStack{TextField(tr("自定义名称，例如：Lishui_Sunrise","Custom name, e.g. Lishui_Sunrise"),text:$model.customPhotoName);Button(tr("应用到所选文件夹","Apply to Selected"),action:model.applyPhotoRename).disabled(model.selectedRenameFolders.isEmpty || model.customPhotoName.trimmingCharacters(in:.whitespaces).isEmpty)}}}.padding(6) }
            HStack{Toggle(tr("复制并保留原文件（推荐）","Copy and keep originals (recommended)"),isOn:$model.copyMode);Picker(tr("目录语言","Folder language"),selection:Binding(get:{model.namingLanguage},set:model.setNamingLanguage)){ForEach(NamingLanguage.allCases){Text($0.rawValue).tag($0)}}.pickerStyle(.segmented).frame(width:210);Spacer();Text("\(tr("目标","Target"))：\(model.output.path)").lineLimit(1).foregroundStyle(.secondary)}
            HStack{Text(tr("日期","Date")).frame(width:90);Text(tr("地区 / 来源","Location / Source")).frame(width:170);Text(tr("设备（可编辑）","Device (editable)")).frame(width:160);Text(tr("类型","Type")).frame(width:50);Text(tr("目标路径","Target Path"));Spacer()}.font(.caption).foregroundStyle(.secondary)
            List(model.records){r in HStack{Text(r.date).frame(width:90,alignment:.leading);VStack(alignment:.leading,spacing:2){TextField("未设置",text:Binding(get:{r.location},set:{model.setManualLocation(r.id,$0)}));Text("来源：\(r.locationSource.label)").font(.caption2).foregroundStyle(.secondary)}.frame(width:170);TextField("设备",text:Binding(get:{r.device},set:{model.setDevice(r.id,$0)})).frame(width:160);Label(r.kind,systemImage:r.kind=="照片" ? "photo":"video").labelStyle(.iconOnly).frame(width:50);VStack(alignment:.leading,spacing:2){Text(r.target).lineLimit(1);if let name=r.outputFileName{Text(name).font(.caption2).foregroundStyle(.secondary)}};Spacer()}}.frame(minHeight:330)
        }
    }
    private func statCard(_ title:String,_ value:Int,_ icon:String)->some View { HStack{Image(systemName:icon).font(.title2).foregroundStyle(.tint);VStack(alignment:.leading){Text("\(value)").font(.title2.bold());Text(title).font(.caption).foregroundStyle(.secondary)}}.padding(12).frame(maxWidth:.infinity,alignment:.leading).background(Color.secondary.opacity(0.07)).clipShape(RoundedRectangle(cornerRadius:10)) }

    private var statusPanel:some View { VStack(alignment:.leading,spacing:7){if model.busy && model.progressTotal>0{ProgressView(value:Double(model.progressDone),total:Double(model.progressTotal));HStack{Text("\(model.progressDone)/\(model.progressTotal)");Text(model.currentFile).lineLimit(1);Spacer();if model.failureCount>0{Text("失败/跳过 \(model.failureCount)").foregroundStyle(.orange)}}.font(.caption).foregroundStyle(.secondary)};HStack{Image(systemName:model.busy ? "arrow.triangle.2.circlepath":"info.circle");Text(model.status).lineLimit(2);Spacer()}}.padding(12).background(Color.secondary.opacity(0.06)).clipShape(RoundedRectangle(cornerRadius:10)) }
}
@main struct MaterialOrganizerApp:App{var body:some Scene{WindowGroup("Media Organizer"){ContentView()}}}
#endif
