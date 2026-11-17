from pathlib import Path
import subprocess,json
ROOT=Path(__file__).resolve().parents[1]
STYLE='''skinparam backgroundColor #FFFFFF
skinparam defaultFontName Microsoft YaHei
skinparam defaultFontSize 15
skinparam shadowing false
skinparam roundcorner 8
skinparam ArrowColor #486581
skinparam classBackgroundColor #F1F6FA
skinparam classBorderColor #486581
skinparam componentBackgroundColor #F1F6FA
skinparam componentBorderColor #486581
skinparam usecaseBackgroundColor #F1F6FA
skinparam usecaseBorderColor #486581
skinparam sequenceMessageAlign center
skinparam maxMessageSize 260
skinparam dpi 150
'''
DIAGRAMS={
'01_组件图':('结构性图','模块架构与协作',r'''
!pragma layout smetana
top to bottom direction
component "参与者 / 组织者 / 检票员 / 管理员界面" as UI
component "应用用例入口\n权限校验 + UnitOfWork事务协调" as APP
package "单实例后端 · 11个逻辑模块" {
component "M01 身份与授权" as M01
component "M02 活动与配置" as M02
component "M03 查询与提醒" as M03
component "M04 订单票据与占位\n统一状态与凭证更新" as M04
component "M05 候补递补" as M05
component "M06 退票与取消联动" as M06
component "M07 电子票转赠" as M07
component "M08 检票与纠错" as M08
component "M09 业务通知" as M09
component "M10 名单与统计" as M10
component "M11 审计记录" as M11
}
database "MySQL\n业务 + 审计 + 待通知事件" as DB
component "本地模拟适配器\n支付 / 退款 / 微信登录与推送" as MOCK
UI --> APP
APP --> M01 : 每次受保护操作
APP --> M02
APP --> M03
APP --> M04
APP --> M06
APP --> M07
APP --> M08
M05 --> M04 : 递补占位
M06 --> M04 : 退款与失效转换
M07 --> M04 : 锁定 / 持票人 / 凭证
M08 --> M04 : 核销状态
M02 --> M04 : 容量下限校验
M03 --> M10 : 查询统一统计口径
APP --> M11 : 同事务审计
APP --> DB : Repository / UnitOfWork
DB --> M09 : 已提交的待通知事件
M04 --> MOCK : 模拟支付
M06 --> MOCK : 模拟退款
M01 --> MOCK : 模拟授权登录
M09 --> MOCK : 模拟订阅推送
note bottom of APP
关键路径用例统一协调；图中只画主要依赖。
业务结果与审计同事务提交；通知不延长支付期限。
模块不是独立部署的微服务。
end note
'''),
'02_用例图_参与者':('行为性图','参与者业务边界',r'''
!pragma layout smetana
left to right direction
actor "访客" as Guest
actor "参与者" as Buyer
Guest <|-- Buyer
rectangle "活动票务与报名系统" {
usecase "组合查询活动与详情" as Q
usecase "登录与管理观演人" as A
usecase "订阅开售提醒" as N
usecase "实名报名 / 选座购票" as B
usecase "校验实名、库存与时段" as V
usecase "模拟支付 / 恢复原订单" as P
usecase "候补登记与退出" as W
usecase "免费取消 / 付费退票" as R
usecase "转赠、接收与原路转回" as T
usecase "查看票据与本人消息" as I
}
Guest --> Q
Buyer --> A
Buyer --> N
Buyer --> B
Buyer --> P
Buyer --> W
Buyer --> R
Buyer --> T
Buyer --> I
B ..> V : <<include>>
note bottom of N : 开售提醒不占名额，也不加入候补队列
note bottom of T : 接收人实名认证；待接收期间锁票；旧凭证永久失效
'''),
'03_用例图_管理与检票':('行为性图','管理端与检票端权限',r'''
!pragma layout smetana
left to right direction
actor "组织者\n指定活动" as O
actor "检票人员\n指定场次" as C
actor "平台管理员" as A
rectangle "管理与现场业务" {
usecase "创建活动、场次、票种\n修改与提交审核" as E
usecase "审核、发布控制与下架" as R
usecase "授权用户与角色范围" as U
usecase "申请取消 / 延期 / 纠错" as X
usecase "审批取消与纠错\n设定退款批次比例" as Y
usecase "在线核销 / 离线核验\n恢复同步" as S
usecase "异常核销复核" as V
usecase "名单导出与容量统计" as D
usecase "查询审计日志" as L
}
O --> E
O --> X
O --> D
C --> S
A --> R
A --> U
A --> Y
A --> V
A --> D
A --> L
note bottom of D
组织者仅本人授权活动且敏感字段脱敏。
检票人员无批量导出权限。
end note
note bottom of Y : 系统自动执行超时、递补、缺席等规则，不视为人工角色
'''),
'04_类图_核心票务':('结构性图','核心领域类及占位约束',r'''
!pragma layout smetana
hide circle
class "活动 Event" as Event {
 - id: UUID
 - status: EventStatus
 + submitReview()
 + applyApprovedChange()
}
class "场次 Session" as Session {
 - id: UUID
 - startsAt: Instant
 - endsAt: Instant
 - salesStatus: SalesStatus
 + assertSaleAllowed(now)
}
class "票种 TicketType" as Type {
 - capacity: int
 - price: Decimal
 + validateCapacity(occupied)
}
class "场次座位 SessionSeat" as Seat {
 - id: UUID
 - zone: String
 - label: String
}
class "主订单 Order" as Order {
 - requestId: UUID
 - buyerId: UUID
 - payDeadline: Instant
 + submitAtomically(items)
}
class "子票单 Ticket" as Ticket {
 - id: UUID
 - spectatorKey: HMAC
 - holderId: UUID
 - paidPrice: Decimal
 - ruleSnapshot: JSON
 - state: TicketState
 - transferLocked: boolean
 + transition(expectedState, target)
 + replaceCredential()
}
class "有效占位 ActiveClaim" as Claim {
 - sessionId: UUID
 - identityKey: HMAC
 - seatId: UUID?
 + releaseOnce()
}
class "检票凭证 Credential" as Credential {
 - tokenDigest: String
 - valid: boolean
 + revokePermanently()
}
class "票据应用服务 TicketService" as Service {
 + createOrder(request)
 + applyPayment(result)
 + expirePayment(orderId)
 + reserveForWaitlist(entryId)
 + mutateTicket(command)
}
Event "1" *-- "1..*" Session
Session "1" *-- "1..*" Type
Session "1" *-- "0..*" Seat
Order "1" *-- "1..4" Ticket
Order "0..*" --> "1" Session : 仅一个场次
Ticket "0..*" --> "1" Type
Ticket "0..*" --> "0..1" Seat : 历史可重复关联
Ticket "1" *-- "0..*" Credential
Ticket "1" -- "0..1" Claim : 当前有效占位
Service ..> Order
Service ..> Ticket
Service ..> Claim
note bottom of Claim
UNIQUE(sessionId, identityKey)
UNIQUE(sessionId, seatId) [非空]
已报名、已检票、已缺席、待付、退票中持有占位。
已取消、已退票或取消场次失效后不再持有有效占位。
end note
note bottom of Ticket
原购票人由主订单关联；当前持票人与原付款账户分开。
历史凭证可有多个，但有效凭证最多一个。
end note
'''),
'05_类图_身份与业务记录':('结构性图','身份授权与可追溯记录',r'''
!pragma layout smetana
hide circle
class "用户 User" as U {
 - id: UUID
 - accountKind: AccountKind
 + canAccess(scope)
}
class "授权 RoleGrant" as G {
 - role: Role
 - activityId: UUID?
 - sessionId: UUID?
}
class "实名身份 Identity" as I {
 - identityKey: HMAC
 - encryptedId: Bytes
 - encryptedPhone: Bytes
}
class "候补 WaitEntry" as W {
 - sessionId: UUID
 - typeId: UUID
 - queueSeq: long
 - status: WaitStatus
 + promote()
}
class "主订单 Order" as O
class "子票单 Ticket" as T
class "支付流水 Payment" as P {
 - orderId: UUID
 - providerTxnId: String
 - originalAccount: String
 - status: PaymentStatus
 + applyOnce()
}
class "退款批次 RefundBatch" as B {
 - sessionId: UUID
 - ratio: Decimal
 - reason: String
 - frozenAt: Instant?
 + startAndFreeze()
}
class "退款 Refund" as R {
 - refundKey: UUID
 - amount: Decimal
 - status: RefundStatus
 + retrySameRefund()
}
class "转赠 Transfer" as X {
 - fromUser: UUID
 - toUser: UUID
 - expiresAt: Instant
 - status: TransferStatus
 + acceptOrReturn()
}
class "核销事实 CheckIn" as C {
 - deviceEventId: UUID
 - occurredAt: Instant
 - syncResult: SyncStatus
}
class "纠错 Correction" as K {
 - applicantId: UUID
 - approverId: UUID?
 - reason: String
}
class "通知 Notification" as N {
 - recipientId: UUID
 - objectId: UUID
 - state: MessageState
}
class "审计 AuditLog" as A {
 - actor: String
 - action: String
 - beforeAfter: JSON
 - occurredAt: Instant
}
U "1" *-- "0..*" G
U "0..*" -- "0..*" I : 可代他人购票
W "0..*" --> "1" I
T "0..*" --> "1" I : 当前观演身份
O "1" *-- "1..4" T
O "1" <-- "0..*" P : 归属订单
P "1" <-- "0..*" R : 退原账户
B "0..1" <-- "0..*" R
T "1" <-- "0..*" R
T "1" <-- "0..*" X
T "1" <-- "0..*" C
C "0..1" <-- "0..*" K
U "1" <-- "0..*" N
N -[hidden]down- A
note top of P
orderId外键指向主订单
每条流水只归属一个订单
保留历史流水，结果不得重复应用
end note
note bottom of A
审计对象用类型+ID关联业务
仅管理员查询，不可修改删除
end note
note bottom of B
执行前可调0%~100%
执行后冻结，重试沿用同一比例
end note
'''),
'06_状态图_子票单':('行为性图','票据状态与受控例外',r'''
!pragma layout smetana
state "待支付" as Pending
state "已报名" as Valid
state "退票中" as Refunding
state "已退票" as Refunded
state "已取消" as Cancelled
state "已检票" as Checked
state "已缺席" as Absent
state "已失效\n场次取消" as Invalid
[*] --> Pending : 收费占位成功
[*] --> Valid : 免费报名成功
Pending --> Valid : 期限内有效付款结果
Pending --> Cancelled : 未付款超时 / 取消场次关闭待付
Valid --> Refunding : 合法付费退票申请
Refunding --> Refunded : 普通退款成功
Refunding --> Valid : 普通退款失败且场次仍有效
Valid --> Cancelled : 合法免费取消
Valid --> Checked : 授权时段内核销成功
Valid --> Absent : 演出结束未检票
Absent --> Checked : 合法离线事实迟到同步
Checked --> Valid : 管理员批准纠错
Absent --> Valid : 管理员批准纠错
Valid --> Invalid : 取消场次
Refunding --> Invalid : 取消场次
Checked --> Invalid : 取消场次
Absent --> Invalid : 取消场次
note bottom of Valid
转赠待接收是独立锁定，不新增票据枚举：
禁止核销、退票、二次转赠；成功只换持票人与凭证。
撤回/拒绝/到期按当前场次有效性解锁。
end note
note bottom of Invalid
取消退款进度独立记录；失败不恢复票据。
旧核销事实保留；迟到离线同步不复活资格。
已退票、已取消和已失效不能普通回退。
end note
'''),
'07_时序图_整单下单与支付':('交互性图','幂等下单与支付结果处理',r'''
autonumber
actor "参与者" as U
boundary "购票界面" as UI
control "下单用例 / M04" as S
database "MySQL" as DB
participant "模拟支付" as P
U -> UI : 同场次选观演人、票种和座位
UI -> S : createOrder(requestId, items[1..4])
S -> DB : BEGIN；查幂等结果；锁场次行
alt 已有同请求结果
 DB --> S : 原订单或当前处理结果
 S -> DB : 结束只读/无变更事务
 S --> UI : 返回原结果，不重复占位
else 新请求
 S -> DB : 校验权限、最新可售时段、实名与座位
 alt 任一子票冲突
  S -> DB : ROLLBACK
  S --> UI : 整单失败与业务原因
 else 全部合法
  S -> DB : 同事务创建主子单、快照、占位\n审计和待通知事件；COMMIT
  S --> UI : 免费已报名 / 收费待付15分钟
 end
end
U -> P : 选择模拟支付结果
P -> S : result(txnId, paidAt, orderId)
S -> DB : BEGIN；锁场次/订单；检查流水唯一和当前状态
alt 已取消并释放名额
 S -> DB : 记录迟到支付及异常退款任务\n不恢复票据；审计后COMMIT
else 同流水重复
 S -> DB : 不重复出票；结束事务
else 付款有效且订单待付
 S -> DB : 待付转已报名，占位不增减\n保存流水、审计与通知；COMMIT
end
S --> UI : 可查询最终订单结果
note over S,DB : 支付调用不持有数据库事务锁；结果应用另开短事务
'''),
'08_时序图_超时与候补':('交互性图','释放名额时保持候补优先',r'''
autonumber
participant "超时任务" as T
control "用例协调 / M04" as S
control "M05 候补" as W
database "MySQL" as DB
control "M09 通知" as N
T -> S : expire(orderId)
S -> DB : BEGIN；按统一顺序锁场次、订单
alt 已付款或已处理
 S -> DB : 不改变占位；结束事务
else 确认未付且已到期
 S -> DB : 待付转已取消，释放一次
 S -> W : promoteReleasedCapacity(sessionId, typeId)
 W -> DB : 检查仍可递补；取同场同票种最小有效队列号
 alt 已截止或场次取消
  W -> DB : 不创建递补订单；标记应失效候补
 else 有合法候补
  W -> DB : 复核实名和座位；原子创建递补子票\n免费已报名 / 收费待付15分钟
  W -> DB : 清理成功者同场其他候补
 end
 S -> DB : 写审计和待通知事件；COMMIT
end
DB -> N : 提交后读取待通知事件
N -> N : 生成站内递补消息与模拟推送
note over S,DB
直接购票使用相同场次锁和候补优先检查。
库存释放与候补分配之间不暴露可被抢走的空档。
未确认的候补座位选择策略作为接口保留。
end note
'''),
'09_时序图_转赠与检票竞争':('交互性图','转赠锁定和新旧凭证互斥',r'''
autonumber
actor "原购票人" as A
actor "接收人" as B
control "M07 转赠用例" as X
control "M04 票据服务" as S
database "MySQL" as DB
A -> X : 发起转赠(ticketId, receiver)
X -> DB : BEGIN；锁场次与票据
X -> S : 校验开关、付费有效未检票、次数和截止
X -> DB : 保存申请并锁票；expiresAt=min(24h, T-30m)\n审计并COMMIT
B -> X : 确认接收
X -> DB : BEGIN；锁同场次和票据；复核申请未终止
X -> S : 校验实名、截止与全局同场占位唯一
alt 校验失败 / 已撤回或已截止
 X -> DB : 不换持票人；按规则处理终止与解锁\n已取消场次保持失效；审计后COMMIT
else 校验通过
 X -> DB : 迁移实名占位，换持票人\n旧凭证永久撤销，新凭证唯一有效
 X -> DB : 保存转赠历史；向外成功次数+1\n审计与通知事件；COMMIT
end
S -> DB : 核销请求也锁同场次与票据
DB --> S : 依据当前锁定和凭证版本校验
note over S,DB
待接收期间拒绝检票/退票/二次转赠。
接收、撤回、到期、核销串行检查当前状态。
原路返还仍受截止和实名约束，不重置次数、不复活旧凭证。
end note
'''),
'10_时序图_取消与退款批次':('交互性图','取消资格与退款执行分离',r'''
autonumber
actor "管理员" as A
control "M06 取消用例" as S
database "MySQL" as DB
participant "模拟退款" as P
control "M09 通知" as N
A -> S : 批准/直接取消场次，填写原因
S -> DB : BEGIN；锁场次；设取消标志\n停止售票、递补、核销、转赠；审计后COMMIT
S -> DB : 分批、幂等关闭待付/候补/转赠\n有效票置失效，保留核销历史
A -> S : 执行前设置已检票退款比例与原因
S -> DB : 新事务校验批次未启动\n保存0%~100%及通知、审计
A -> S : 启动退款批次
S -> DB : 锁批次并冻结比例\n按子票生成唯一退款任务；COMMIT
loop 每个应退子票 / 同笔失败重试
 S -> P : refund(refundKey, 原支付账户, 冻结金额)
 P --> S : 成功/失败
 S -> DB : 新短事务应用唯一结果\n保存流水与审计，失败也不恢复资格
end
DB -> N : 取消原因、比例和退款进度
note over S,DB
主办方原因进行中取消：已检票付费默认全额，免费不退款。
完全结束后已检票/缺席不退；其他原因不可自动套用。
0%是确定的零退款；批次启动后拒绝改比例和重复支付。
场次取消标志使尚未分批更新的票也立即无法核销。
end note
'''),
'11_部署图':('结构性图','课程原型的本地部署',r'''
!pragma layout smetana
node "本地笔记本\n8核 / 16GB / SSD\nWindows 11 或 macOS 14" {
node "浏览器 / 手机视口" as B
node "单实例后端" as S {
artifact "11模块应用 + 定时任务\n本地模拟适配器" as APP
}
database "MySQL\n业务、审计、通知待处理记录" as DB
folder "离线检票端本地缓存\n下载/有效期策略待澄清" as CACHE
}
B --> S : localhost API\n生产部署另用HTTPS
S --> DB : 本地数据库连接
B --> CACHE : 断网核验与待上传记录
note bottom of CACHE : 不能实时撤权、感知转赠或跨设备去重；联网后复核
note bottom of DB : 图为后续原型部署设计，不表示已实现或完成压测
''')}

def generate():
    out=ROOT/'UML';out.mkdir(exist_ok=True)
    catalog=[]
    for stem,(kind,title,body) in DIAGRAMS.items():
        text='@startuml\n'+STYLE+'title '+title+'\n'+body.strip()+'\n@enduml\n'
        (out/(stem+'.puml')).write_text(text,encoding='utf-8')
        catalog.append({'id':stem[:2],'file':stem,'kind':kind,'title':title})
    (out/'目录.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Wrote',len(catalog),'PlantUML sources.')

if __name__=='__main__':generate()
