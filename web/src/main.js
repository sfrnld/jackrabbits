import './tokens.css'
import { mount } from 'svelte'
import App from './App.svelte'
import { initTips } from './lib/glossary.js'
initTips()
mount(App, { target: document.getElementById('app') })
