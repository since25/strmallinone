搜索接口示例
curl 'http://192.168.70.120:8008/api/search?keyword=%E7%96%AF%E7%8B%82%E5%8A%A8%E7%89%A9%E5%9F%8E&lastMessageId=' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'Accept-Language: zh-CN,zh;q=0.9,en;q=0.8' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiJlNjMzMzllYS05ZDRlLTQwMzEtOTRhNi1hNTY3NDg0NDIwM2IiLCJyb2xlIjoxLCJpYXQiOjE3NzMxMjU2MjUsImV4cCI6MTc3MzE0NzIyNX0.WZp4_d3mgYgA61U7W5rO7gNP5dL1q49GYPie6bXiDo0' \
  -H 'Connection: keep-alive' \
  -b 'MoviePilot=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzMxMjMzNjgsImlhdCI6MTc3MzEyMTU2OCwic3ViIjoiMSIsInVzZXJuYW1lIjoiYWRtaW4iLCJzdXBlcl91c2VyIjp0cnVlLCJsZXZlbCI6MiwicHVycG9zZSI6InJlc291cmNlIn0.KX847kbuBUSnNzamyJramH9-KMEvcp50VBaPpuIMIik' \
  -H 'If-None-Match: W/"fdda-D01XXKWoPStF2pyT0ER9VE4ea24"' \
  -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36' \
  --insecure

任意点击一个资源的转存按钮
curl 'http://192.168.70.120:8008/api/cloud115/share-info?shareCode=swwil5i3h88&receiveCode=LGNB' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'Accept-Language: zh-CN,zh;q=0.9,en;q=0.8' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiJlNjMzMzllYS05ZDRlLTQwMzEtOTRhNi1hNTY3NDg0NDIwM2IiLCJyb2xlIjoxLCJpYXQiOjE3NzMxMjU2MjUsImV4cCI6MTc3MzE0NzIyNX0.WZp4_d3mgYgA61U7W5rO7gNP5dL1q49GYPie6bXiDo0' \
  -H 'Connection: keep-alive' \
  -b 'MoviePilot=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzMxMjMzNjgsImlhdCI6MTc3MzEyMTU2OCwic3ViIjoiMSIsInVzZXJuYW1lIjoiYWRtaW4iLCJzdXBlcl91c2VyIjp0cnVlLCJsZXZlbCI6MiwicHVycG9zZSI6InJlc291cmNlIn0.KX847kbuBUSnNzamyJramH9-KMEvcp50VBaPpuIMIik' \
  -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36' \
  --insecure

选择下一步，保存的网盘目录（当前为默认数值，应该是上一次保存的目录）
curl 'http://192.168.70.120:8008/api/cloud115/folders?parentCid=0' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'Accept-Language: zh-CN,zh;q=0.9,en;q=0.8' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiJlNjMzMzllYS05ZDRlLTQwMzEtOTRhNi1hNTY3NDg0NDIwM2IiLCJyb2xlIjoxLCJpYXQiOjE3NzMxMjU2MjUsImV4cCI6MTc3MzE0NzIyNX0.WZp4_d3mgYgA61U7W5rO7gNP5dL1q49GYPie6bXiDo0' \
  -H 'Connection: keep-alive' \
  -b 'MoviePilot=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzMxMjMzNjgsImlhdCI6MTc3MzEyMTU2OCwic3ViIjoiMSIsInVzZXJuYW1lIjoiYWRtaW4iLCJzdXBlcl91c2VyIjp0cnVlLCJsZXZlbCI6MiwicHVycG9zZSI6InJlc291cmNlIn0.KX847kbuBUSnNzamyJramH9-KMEvcp50VBaPpuIMIik' \
  -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36' \
  --insecure

选择automv（如果资源类型是电视剧，应该选择autotv）
curl 'http://192.168.70.120:8008/api/cloud115/folders?parentCid=3374320430729920485' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'Accept-Language: zh-CN,zh;q=0.9,en;q=0.8' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiJlNjMzMzllYS05ZDRlLTQwMzEtOTRhNi1hNTY3NDg0NDIwM2IiLCJyb2xlIjoxLCJpYXQiOjE3NzMxMjU2MjUsImV4cCI6MTc3MzE0NzIyNX0.WZp4_d3mgYgA61U7W5rO7gNP5dL1q49GYPie6bXiDo0' \
  -H 'Connection: keep-alive' \
  -b 'MoviePilot=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzMxMjMzNjgsImlhdCI6MTc3MzEyMTU2OCwic3ViIjoiMSIsInVzZXJuYW1lIjoiYWRtaW4iLCJzdXBlcl91c2VyIjp0cnVlLCJsZXZlbCI6MiwicHVycG9zZSI6InJlc291cmNlIn0.KX847kbuBUSnNzamyJramH9-KMEvcp50VBaPpuIMIik' \
  -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36' \
  --insecure

save动作
curl 'http://192.168.70.120:8008/api/cloud115/save' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'Accept-Language: zh-CN,zh;q=0.9,en;q=0.8' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiJlNjMzMzllYS05ZDRlLTQwMzEtOTRhNi1hNTY3NDg0NDIwM2IiLCJyb2xlIjoxLCJpYXQiOjE3NzMxMjU2MjUsImV4cCI6MTc3MzE0NzIyNX0.WZp4_d3mgYgA61U7W5rO7gNP5dL1q49GYPie6bXiDo0' \
  -H 'Connection: keep-alive' \
  -H 'Content-Type: application/json' \
  -b 'MoviePilot=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzMxMjMzNjgsImlhdCI6MTc3MzEyMTU2OCwic3ViIjoiMSIsInVzZXJuYW1lIjoiYWRtaW4iLCJzdXBlcl91c2VyIjp0cnVlLCJsZXZlbCI6MiwicHVycG9zZSI6InJlc291cmNlIn0.KX847kbuBUSnNzamyJramH9-KMEvcp50VBaPpuIMIik' \
  -H 'Origin: http://192.168.70.120:8008' \
  -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36' \
  --data-raw '{"shareCode":"swwil5i3h88","receiveCode":"LGNB","fileId":"3196702367014317096","folderId":"3374320430729920485","fids":["3196702367014317096"]}' \
  --insecure

从cloudsaver中触发strm_webhook服务
curl 'http://192.168.70.120:8008/api/plugins/run' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'Accept-Language: zh-CN,zh;q=0.9,en;q=0.8' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiJlNjMzMzllYS05ZDRlLTQwMzEtOTRhNi1hNTY3NDg0NDIwM2IiLCJyb2xlIjoxLCJpYXQiOjE3NzMxMjU2MjUsImV4cCI6MTc3MzE0NzIyNX0.WZp4_d3mgYgA61U7W5rO7gNP5dL1q49GYPie6bXiDo0' \
  -H 'Connection: keep-alive' \
  -H 'Content-Type: application/json' \
  -b 'MoviePilot=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzMxMjMzNjgsImlhdCI6MTc3MzEyMTU2OCwic3ViIjoiMSIsInVzZXJuYW1lIjoiYWRtaW4iLCJzdXBlcl91c2VyIjp0cnVlLCJsZXZlbCI6MiwicHVycG9zZSI6InJlc291cmNlIn0.KX847kbuBUSnNzamyJramH9-KMEvcp50VBaPpuIMIik' \
  -H 'Origin: http://192.168.70.120:8008' \
  -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36' \
  --data-raw $'{"id":4,"builtInParams":{"title":"名称: [LGNB全球顶级封装][疯狂动物城][4K-REMUX][DIY杜比视界+HDR][英语+台配国语+中影国语+粤语+日语+韩语+泰语+法语+西班牙语+葡萄牙语][中英特效字幕+台配国语特效字幕+中影国语特效字幕+官方中文字幕]","firstShareUrl":"https://115cdn.com/s/swwil5i3h88?password=LGNB&amp;#","shareUrlStr":"网盘（pan115）:https://115cdn.com/s/swwil5i3h88?password=LGNB&amp;#","description":"名称: [LGNB全球顶级封装][<mark class=\\"highlight\\">疯狂动物城</mark>][4K-REMUX][DIY杜比视界+HDR][英语+台配国语+中影国语+粤语+日语+韩语+泰语+法语+西班牙语+葡萄牙语][中英特效字幕+台配国语特效字幕+中影国语特效字幕+官方中文字幕]发行时间: 2016-02-11剧情简介: 疯狂动物城是一座独一无二的现代动物都市。每种动物在这里都有自己的居所，比如富丽堂皇的撒哈拉广场，或者常年严寒的冰川镇。它就像一座大熔炉，动物们在这里和平共处——无论是大象还是小老鼠，只要你努力，都能在此闯出一番名堂。不过乐观的警官兔朱迪（金妮弗·古德温 Ginnifer Goodwin 配音）却发现，作为史上第一任兔子警官，要和一群强硬的大块头动物警察合作可不是件容易事。为了证明自己，她决心侦破一桩神秘案件；追寻真相的路上她被迫与口若悬河、谎技高超的狐尼克（杰森·贝特曼 Jason Bateman 配音）联手，却发现这桩案件背后隐藏着一个意欲颠覆动物城的巨大阴谋……<i class=\\"emoji\\" style=\\"background-image:url(\'//telegram.org/img/emoji/40/F09F9497.png\')\\"><b>🔗</b></i>链接:","shareUrl":"https://115cdn.com/s/swwil5i3h88?password=LGNB&amp;#","shareTitle":"","savePath":"automv","saveFid":"3374320430729920485","shareFid":""}}' \
  --insecure

cloudsaver返回状态：成功（不确定是不是这个）
blob:http://192.168.70.120:8008/86832a97-aec2-4a51-867f-6c59a65a237c