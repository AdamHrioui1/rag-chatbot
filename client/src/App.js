import React from 'react'
import Routers from './Routers'
import { ContextProvider } from './ContextApi'

function App() {
    return (
        <ContextProvider>
            <Routers />
        </ContextProvider>
    )
}

export default App