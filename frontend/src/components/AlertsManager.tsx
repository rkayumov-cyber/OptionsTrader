import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Loader2,
  Plus,
  X,
  Bell,
  BellOff,
  AlertTriangle,
  Check,
  Trash2,
  Settings,
  CheckCheck,
} from "lucide-react"
import {
  useAlertRules,
  useAlertNotifications,
  useUnacknowledgedAlerts,
  useCreateAlertRule,
  useDeleteAlertRule,
  useToggleAlertRule,
  useAcknowledgeAlert,
  useAcknowledgeAllAlerts,
  useDeleteAlertNotification,
} from "@/hooks/useMarketData"
import type { Market, AlertRuleType, AlertRule, AlertNotification } from "@/lib/api"

interface AlertsManagerProps {
  className?: string
}

const RULE_TYPE_LABELS: Record<AlertRuleType, string> = {
  price_above: "Price Above",
  price_below: "Price Below",
  iv_rank_above: "IV Rank Above",
  iv_rank_below: "IV Rank Below",
  volume_above: "Volume Above",
  pc_ratio_above: "P/C Ratio Above",
  pc_ratio_below: "P/C Ratio Below",
}

const SEVERITY_COLORS: Record<string, string> = {
  info: "bg-bb-blue/20 text-bb-blue",
  warning: "bg-bb-amber/20 text-bb-amber",
  critical: "bg-bb-red/20 text-bb-red",
}

export function AlertsManager({ className }: AlertsManagerProps) {
  const [activeTab, setActiveTab] = useState("notifications")
  const [showAddForm, setShowAddForm] = useState(false)
  const [newRule, setNewRule] = useState({
    symbol: "",
    market: "US" as Market,
    rule_type: "price_above" as AlertRuleType,
    threshold: 0,
  })

  const { data: rules, isLoading: rulesLoading } = useAlertRules()
  const { data: notifications, isLoading: notificationsLoading } = useAlertNotifications()
  const { data: unacknowledged } = useUnacknowledgedAlerts()
  const createRule = useCreateAlertRule()
  const deleteRule = useDeleteAlertRule()
  const toggleRule = useToggleAlertRule()
  const acknowledgeAlert = useAcknowledgeAlert()
  const acknowledgeAll = useAcknowledgeAllAlerts()
  const deleteNotification = useDeleteAlertNotification()

  const handleCreateRule = () => {
    if (!newRule.symbol || newRule.threshold <= 0) return
    createRule.mutate(newRule, {
      onSuccess: () => {
        setShowAddForm(false)
        setNewRule({
          symbol: "",
          market: "US",
          rule_type: "price_above",
          threshold: 0,
        })
      },
    })
  }

  const unacknowledgedCount = unacknowledged?.length || 0

  if (rulesLoading || notificationsLoading) {
    return (
      <Card className={className}>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg">Alerts</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <CardTitle className="text-lg flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span>Alerts</span>
            {unacknowledgedCount > 0 && (
              <span className="bg-bb-red text-white text-[10px] px-1.5 py-0.5 rounded-full">
                {unacknowledgedCount}
              </span>
            )}
          </div>
          <Button variant="outline" size="sm" onClick={() => setShowAddForm(!showAddForm)}>
            {showAddForm ? <X className="h-3.5 w-3.5 mr-1" /> : <Plus className="h-3.5 w-3.5 mr-1" />}
            {showAddForm ? "Cancel" : "New Rule"}
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid grid-cols-2 w-full mb-3">
            <TabsTrigger value="notifications" className="text-xs gap-1.5 relative">
              <Bell className="h-3.5 w-3.5" />
              Notifications
              {unacknowledgedCount > 0 && (
                <span className="absolute -top-1 -right-1 bg-bb-red text-white text-[10px] w-4 h-4 rounded-full flex items-center justify-center">
                  {unacknowledgedCount}
                </span>
              )}
            </TabsTrigger>
            <TabsTrigger value="rules" className="text-xs gap-1.5">
              <Settings className="h-3.5 w-3.5" />
              Rules ({rules?.length || 0})
            </TabsTrigger>
          </TabsList>

          <TabsContent value="notifications" className="mt-4">
            {unacknowledgedCount > 0 && (
              <div className="flex justify-end mb-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => acknowledgeAll.mutate()}
                  disabled={acknowledgeAll.isPending}
                >
                  <CheckCheck className="h-3.5 w-3.5 mr-1" />
                  Acknowledge All
                </Button>
              </div>
            )}

            {notifications && notifications.length > 0 ? (
              <div className="space-y-2 max-h-[480px] overflow-y-auto">
                {notifications.map((notification: AlertNotification) => (
                  <div
                    key={notification.id}
                    className={`border border-border rounded-lg p-3 ${notification.acknowledged ? "bg-muted/20 opacity-60" : "bg-muted/40"}`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        <span className={`text-[10px] px-1.5 py-0.5 rounded ${SEVERITY_COLORS[notification.severity]}`}>
                          {notification.severity.toUpperCase()}
                        </span>
                        <span className="font-bold">{notification.symbol}</span>
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-muted">{notification.market}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        {!notification.acknowledged && (
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => acknowledgeAlert.mutate(notification.id)}
                          >
                            <Check className="h-3.5 w-3.5 text-bb-green" />
                          </Button>
                        )}
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => deleteNotification.mutate(notification.id)}
                        >
                          <Trash2 className="h-3.5 w-3.5 text-destructive" />
                        </Button>
                      </div>
                    </div>
                    <p className="text-sm">{notification.message}</p>
                    <div className="flex items-center justify-between mt-2 text-xs text-muted-foreground">
                      <span>
                        Current: {notification.current_value.toFixed(2)} | Threshold: {notification.threshold.toFixed(2)}
                      </span>
                      <span>{new Date(notification.triggered_at).toLocaleString()}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-32 text-muted-foreground">
                <Bell className="h-8 w-8 mb-2 opacity-50" />
                <p className="text-sm">No notifications</p>
                <p className="text-xs text-muted-foreground mt-1">Alerts will appear here when triggered</p>
              </div>
            )}
          </TabsContent>

          <TabsContent value="rules" className="mt-4">
            {/* Add Rule Form */}
            {showAddForm && (
              <div className="border border-border rounded-lg p-4 space-y-3 bg-muted/30 mb-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <Input
                    placeholder="Symbol"
                    value={newRule.symbol}
                    onChange={(e) => setNewRule({ ...newRule, symbol: e.target.value.toUpperCase() })}
                    className="h-8"
                  />
                  <Select
                    value={newRule.market}
                    onChange={(e) => setNewRule({ ...newRule, market: e.target.value as Market })}
                    className="h-8"
                  >
                    <option value="US">US</option>
                    <option value="JP">JP</option>
                    <option value="HK">HK</option>
                  </Select>
                  <Select
                    value={newRule.rule_type}
                    onChange={(e) => setNewRule({ ...newRule, rule_type: e.target.value as AlertRuleType })}
                    className="h-8"
                  >
                    {Object.entries(RULE_TYPE_LABELS).map(([value, label]) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </Select>
                  <Input
                    type="number"
                    placeholder="Threshold"
                    value={newRule.threshold || ""}
                    onChange={(e) => setNewRule({ ...newRule, threshold: parseFloat(e.target.value) || 0 })}
                    className="h-8"
                  />
                </div>
                <Button onClick={handleCreateRule} disabled={createRule.isPending} className="w-full mt-2">
                  {createRule.isPending && <Loader2 className="h-3.5 w-3.5 animate-spin mr-2" />}
                  Create Alert Rule
                </Button>
              </div>
            )}

            {/* Rules List */}
            {rules && rules.length > 0 ? (
              <div className="space-y-2 max-h-[480px] overflow-y-auto">
                {rules.map((rule: AlertRule) => (
                  <div key={rule.id} className="border border-border rounded-lg p-3 bg-muted/20 hover:bg-muted/30 transition-colors">
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        <span className="font-bold">{rule.symbol}</span>
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-muted">{rule.market}</span>
                        <span className="text-xs text-muted-foreground">{RULE_TYPE_LABELS[rule.rule_type]}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => toggleRule.mutate(rule.id)}
                        >
                          {rule.enabled ? (
                            <Bell className="h-3.5 w-3.5 text-bb-green" />
                          ) : (
                            <BellOff className="h-3.5 w-3.5 text-muted-foreground" />
                          )}
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => deleteRule.mutate(rule.id)}
                        >
                          <Trash2 className="h-3.5 w-3.5 text-destructive" />
                        </Button>
                      </div>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span>
                        Threshold: <span className="font-semibold tabular-nums">{rule.threshold}</span>
                      </span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded ${rule.enabled ? "bg-bb-green/20 text-bb-green" : "bg-bb-muted/20 text-bb-muted"}`}>
                        {rule.enabled ? "ACTIVE" : "DISABLED"}
                      </span>
                    </div>
                    {rule.trigger_count > 0 && (
                      <div className="text-xs text-muted-foreground mt-1">
                        Triggered {rule.trigger_count} times
                        {rule.last_triggered && ` | Last: ${new Date(rule.last_triggered).toLocaleDateString()}`}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-32 text-muted-foreground">
                <AlertTriangle className="h-8 w-8 mb-2 opacity-50" />
                <p className="text-sm">No alert rules</p>
                <p className="text-xs text-muted-foreground mt-1">Create rules to get notified</p>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}
