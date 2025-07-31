'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { OverviewDashboard } from './overview-dashboard'
import { AgentsMonitoring } from './agents-monitoring'
import { TasksManagement } from './tasks-management'
import { SimulationCenter } from './simulation-center'
import { SecurityMonitoring } from './security-monitoring'

export function MainContent() {
  const [activeTab, setActiveTab] = useState('overview')

  const tabs = [
    {
      id: 'overview',
      label: 'Overview',
      component: OverviewDashboard,
    },
    {
      id: 'agents',
      label: 'Agents',
      component: AgentsMonitoring,
    },
    {
      id: 'tasks',
      label: 'Tasks',
      component: TasksManagement,
    },
    {
      id: 'simulation',
      label: 'Simulation',
      component: SimulationCenter,
    },
    {
      id: 'security',
      label: 'Security',
      component: SecurityMonitoring,
    },
  ]

  return (
    <div className="flex flex-col h-full">
      {/* Tab Navigation */}
      <div className="border-b border-slate-800/50 bg-muted/30 backdrop-blur-sm">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="h-12 w-full justify-start rounded-none border-0 bg-transparent p-0">
            {tabs.map((tab) => (
              <TabsTrigger
                key={tab.id}
                value={tab.id}
                className={`
                  relative h-12 rounded-none border-b-2 border-transparent px-6 
                  text-muted-foreground transition-all duration-200
                  data-[state=active]:border-primary data-[state=active]:text-white
                  data-[state=active]:bg-primary/10
                  hover:text-white hover:bg-muted/50
                `}
              >
                {tab.label}
                {/* Active indicator */}
                {activeTab === tab.id && (
                  <motion.div
                    layoutId="activeTab"
                    className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary"
                    transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                  />
                )}
              </TabsTrigger>
            ))}
          </TabsList>

          {/* Tab Content */}
          <div className="flex-1 overflow-hidden">
            <AnimatePresence mode="wait">
              {tabs.map((tab) => (
                <TabsContent
                  key={tab.id}
                  value={tab.id}
                  className="h-full m-0 data-[state=inactive]:hidden"
                >
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.2 }}
                    className="h-full"
                  >
                    <tab.component />
                  </motion.div>
                </TabsContent>
              ))}
            </AnimatePresence>
          </div>
        </Tabs>
      </div>
    </div>
  )
}