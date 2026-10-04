import json
import logging
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

logger = logging.getLogger("nova.dashboard")

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="fr" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NOVA x MK ARENA | Panel d'Administration</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        aperture: {
                            50: '#f0fdf4',
                            500: '#10b981',
                            600: '#059669',
                            800: '#065f46',
                            900: '#064e3b'
                        },
                        dark: {
                            800: '#181b20',
                            900: '#0f1115',
                            950: '#090a0d'
                        }
                    }
                }
            }
        }
    </script>
    <style>
        .sidebar-item.active {
            background: linear-gradient(90deg, rgba(16, 185, 129, 0.15), transparent);
            border-left: 3px solid #10b981;
            color: #34d399;
        }
        .toggle-checkbox:checked {
            right: 0;
            border-color: #10b981;
        }
        .toggle-checkbox:checked + .toggle-label {
            background-color: #10b981;
        }
    </style>
</head>
<body class="bg-dark-950 text-gray-200 font-sans antialiased min-h-screen flex flex-col md:flex-row">

    <!-- Sidebar Navigation (Style DraftBot) -->
    <aside class="w-full md:w-64 bg-dark-900 border-r border-gray-800 flex flex-col shrink-0">
        <div class="p-6 border-b border-gray-800 flex items-center space-x-3">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 flex items-center justify-center text-white font-black shadow-lg shadow-emerald-900/30">
                <i class="fa-solid fa-robot text-lg"></i>
            </div>
            <div>
                <h1 class="font-extrabold text-white text-lg tracking-wide">NOVA PANEL</h1>
                <span class="text-xs text-emerald-400 font-mono tracking-wider flex items-center gap-1.5">
                    <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span> V2 GLaDOS x DraftBot
                </span>
            </div>
        </div>

        <nav class="flex-1 p-4 space-y-1.5 overflow-y-auto">
            <button onclick="switchTab('overview')" id="btn-overview" class="sidebar-item active w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-sm font-medium text-gray-300 hover:bg-gray-800/60 transition">
                <i class="fa-solid fa-chart-pie w-5 text-center text-emerald-400"></i>
                <span>Vue d'ensemble</span>
            </button>
            <button onclick="switchTab('welcome')" id="btn-welcome" class="sidebar-item w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-sm font-medium text-gray-300 hover:bg-gray-800/60 transition">
                <i class="fa-solid fa-hand-wave w-5 text-center text-emerald-400"></i>
                <span>Bienvenue & Départs</span>
            </button>
            <button onclick="switchTab('moderation')" id="btn-moderation" class="sidebar-item w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-sm font-medium text-gray-300 hover:bg-gray-800/60 transition">
                <i class="fa-solid fa-shield-halved w-5 text-center text-emerald-400"></i>
                <span>Modération & AutoMod</span>
            </button>
            <button onclick="switchTab('tickets')" id="btn-tickets" class="sidebar-item w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-sm font-medium text-gray-300 hover:bg-gray-800/60 transition">
                <i class="fa-solid fa-ticket w-5 text-center text-emerald-400"></i>
                <span>Système de Tickets</span>
            </button>
            <button onclick="switchTab('levels')" id="btn-levels" class="sidebar-item w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-sm font-medium text-gray-300 hover:bg-gray-800/60 transition">
                <i class="fa-solid fa-trophy w-5 text-center text-emerald-400"></i>
                <span>Niveaux & XP</span>
            </button>
            <button onclick="switchTab('tournaments')" id="btn-tournaments" class="sidebar-item w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-sm font-medium text-gray-300 hover:bg-gray-800/60 transition">
                <i class="fa-solid fa-crosshairs w-5 text-center text-emerald-400"></i>
                <span>Tournois MK Arena</span>
            </button>
            <button onclick="switchTab('glados')" id="btn-glados" class="sidebar-item w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-sm font-medium text-gray-300 hover:bg-gray-800/60 transition">
                <i class="fa-solid fa-brain w-5 text-center text-emerald-400"></i>
                <span>Personnalité GLaDOS</span>
            </button>
        </nav>

        <div class="p-4 border-t border-gray-800 text-xs text-gray-500 flex justify-between items-center">
            <span>Serveur : <strong id="server-name" class="text-gray-300">🎮 MK-ARENA</strong></span>
            <button onclick="saveAllSettings()" class="bg-emerald-600 hover:bg-emerald-500 text-white px-3 py-1.5 rounded-lg text-xs font-semibold shadow transition">Sauvegarder</button>
        </div>
    </aside>

    <!-- Main Content Area -->
    <main class="flex-1 p-6 md:p-10 overflow-y-auto">
        <!-- Notification Banner -->
        <div id="save-alert" class="hidden mb-6 p-4 rounded-xl bg-emerald-950/80 border border-emerald-500/40 text-emerald-200 flex items-center justify-between">
            <span class="flex items-center gap-2"><i class="fa-solid fa-circle-check text-emerald-400"></i> Vos modifications ont été appliquées avec succès !</span>
            <button onclick="this.parentElement.classList.add('hidden')" class="text-emerald-400 hover:text-white">&times;</button>
        </div>

        <!-- 1. TAB OVERVIEW -->
        <section id="tab-overview" class="space-y-6">
            <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div>
                    <h2 class="text-2xl font-bold text-white">Tableau de Bord Administratif</h2>
                    <p class="text-sm text-gray-400">Gérez toutes les fonctionnalités de NOVA et configurez votre serveur MK ARENA.</p>
                </div>
                <div class="flex gap-2">
                    <button onclick="fetchStats()" class="px-4 py-2 rounded-lg bg-dark-800 hover:bg-gray-800 border border-gray-700 text-xs font-medium text-gray-300 flex items-center gap-2 transition">
                        <i class="fa-solid fa-rotate text-emerald-400"></i> Actualiser
                    </button>
                </div>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div class="bg-dark-900 border border-gray-800 p-5 rounded-xl">
                    <div class="flex justify-between items-center text-gray-400 mb-2">
                        <span class="text-xs uppercase tracking-wider font-semibold">Statut du Bot</span>
                        <i class="fa-solid fa-circle-nodes text-emerald-400"></i>
                    </div>
                    <div class="text-2xl font-bold text-white flex items-center gap-2">
                        <span class="w-3 h-3 rounded-full bg-emerald-500"></span> Opérationnel
                    </div>
                    <p class="text-xs text-gray-500 mt-2">Protocole Aperture Science actif</p>
                </div>
                <div class="bg-dark-900 border border-gray-800 p-5 rounded-xl">
                    <div class="flex justify-between items-center text-gray-400 mb-2">
                        <span class="text-xs uppercase tracking-wider font-semibold">Tournois Détectés</span>
                        <i class="fa-solid fa-trophy text-amber-400"></i>
                    </div>
                    <div id="stat-tournaments" class="text-2xl font-bold text-white">0</div>
                    <p class="text-xs text-gray-500 mt-2">Indexés automatiquement</p>
                </div>
                <div class="bg-dark-900 border border-gray-800 p-5 rounded-xl">
                    <div class="flex justify-between items-center text-gray-400 mb-2">
                        <span class="text-xs uppercase tracking-wider font-semibold">Avertissements</span>
                        <i class="fa-solid fa-triangle-exclamation text-rose-400"></i>
                    </div>
                    <div id="stat-warns" class="text-2xl font-bold text-white">0</div>
                    <p class="text-xs text-gray-500 mt-2">Sanctions enregistrées</p>
                </div>
                <div class="bg-dark-900 border border-gray-800 p-5 rounded-xl">
                    <div class="flex justify-between items-center text-gray-400 mb-2">
                        <span class="text-xs uppercase tracking-wider font-semibold">Apprentissages Staff</span>
                        <i class="fa-solid fa-graduation-cap text-sky-400"></i>
                    </div>
                    <div id="stat-knowledge" class="text-2xl font-bold text-white">0</div>
                    <p class="text-xs text-gray-500 mt-2">Connaissances enregistrées</p>
                </div>
            </div>

            <!-- Commandes rapides -->
            <div class="bg-dark-900 border border-gray-800 rounded-xl p-6">
                <h3 class="text-lg font-bold text-white mb-4 flex items-center gap-2">
                    <i class="fa-solid fa-bolt text-emerald-400"></i> Actions Rapides depuis le Panel
                </h3>
                <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <button onclick="triggerAction('sync_tournaments')" class="p-4 bg-dark-800 hover:bg-gray-800 rounded-lg border border-gray-700 text-left transition group">
                        <div class="font-semibold text-white group-hover:text-emerald-400 flex items-center justify-between">
                            <span>Synchroniser les Tournois</span>
                            <i class="fa-solid fa-arrow-right text-xs"></i>
                        </div>
                        <p class="text-xs text-gray-400 mt-1">Re-scanne la catégorie Discord des tournois MK ARENA.</p>
                    </button>
                    <button onclick="triggerAction('sync_slash')" class="p-4 bg-dark-800 hover:bg-gray-800 rounded-lg border border-gray-700 text-left transition group">
                        <div class="font-semibold text-white group-hover:text-emerald-400 flex items-center justify-between">
                            <span>Synchroniser Commandes Slash</span>
                            <i class="fa-solid fa-arrow-right text-xs"></i>
                        </div>
                        <p class="text-xs text-gray-400 mt-1">Met à jour les commandes /nova-status, /warn, /rank sur Discord.</p>
                    </button>
                    <button onclick="switchTab('moderation')" class="p-4 bg-dark-800 hover:bg-gray-800 rounded-lg border border-gray-700 text-left transition group">
                        <div class="font-semibold text-white group-hover:text-emerald-400 flex items-center justify-between">
                            <span>Régler l'AutoMod</span>
                            <i class="fa-solid fa-arrow-right text-xs"></i>
                        </div>
                        <p class="text-xs text-gray-400 mt-1">Configurer la sécurité Anti-Raid et Anti-Liens.</p>
                    </button>
                </div>
            </div>
        </section>

        <!-- 2. TAB WELCOME & GOODBYE -->
        <section id="tab-welcome" class="hidden space-y-6">
            <div>
                <h2 class="text-2xl font-bold text-white">Messages de Bienvenue & Départs</h2>
                <p class="text-sm text-gray-400">Personnalisez l'arrivée et le départ des membres comme sur DraftBot.</p>
            </div>

            <!-- Welcome Config -->
            <div class="bg-dark-900 border border-gray-800 rounded-xl p-6 space-y-5">
                <div class="flex items-center justify-between border-b border-gray-800 pb-4">
                    <div>
                        <h3 class="font-bold text-white">Activer le message de bienvenue</h3>
                        <p class="text-xs text-gray-400">Envoie un message automatique dans le salon choisi à chaque nouvel arrivant.</p>
                    </div>
                    <label class="relative inline-flex items-center cursor-pointer">
                        <input type="checkbox" id="welcome_enabled" class="sr-only peer">
                        <div class="w-11 h-6 bg-gray-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-500"></div>
                    </label>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label class="block text-xs font-semibold text-gray-300 mb-2 uppercase">ID du Salon de Bienvenue</label>
                        <input type="text" id="welcome_channel_id" placeholder="Ex: 123456789012345678" class="w-full bg-dark-800 border border-gray-700 rounded-lg px-4 py-2 text-sm text-white focus:outline-none focus:border-emerald-500">
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-gray-300 mb-2 uppercase">ID du Rôle Automatique (Auto-rôle)</label>
                        <input type="text" id="autorole_id" placeholder="Ex: Rôle Joueur / Membre" class="w-full bg-dark-800 border border-gray-700 rounded-lg px-4 py-2 text-sm text-white focus:outline-none focus:border-emerald-500">
                    </div>
                </div>

                <div>
                    <label class="block text-xs font-semibold text-gray-300 mb-2 uppercase">Message de Bienvenue Personnalisé</label>
                    <textarea id="welcome_message" rows="3" class="w-full bg-dark-800 border border-gray-700 rounded-lg p-3 text-sm text-white focus:outline-none focus:border-emerald-500 font-mono"></textarea>
                    <p class="text-xs text-gray-500 mt-1">Variables disponibles : <code class="text-emerald-400">{user}</code> (mention), <code class="text-emerald-400">{server}</code> (nom du serveur), <code class="text-emerald-400">{count}</code> (nombre de membres).</p>
                </div>
            </div>

            <!-- Leave Config -->
            <div class="bg-dark-900 border border-gray-800 rounded-xl p-6 space-y-5">
                <div class="flex items-center justify-between border-b border-gray-800 pb-4">
                    <div>
                        <h3 class="font-bold text-white">Activer le message d'au revoir</h3>
                        <p class="text-xs text-gray-400">Alerte le serveur quand un membre s'en va.</p>
                    </div>
                    <label class="relative inline-flex items-center cursor-pointer">
                        <input type="checkbox" id="leave_enabled" class="sr-only peer">
                        <div class="w-11 h-6 bg-gray-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-500"></div>
                    </label>
                </div>

                <div>
                    <label class="block text-xs font-semibold text-gray-300 mb-2 uppercase">ID du Salon de Départ</label>
                    <input type="text" id="leave_channel_id" placeholder="Ex: 123456789012345678" class="w-full bg-dark-800 border border-gray-700 rounded-lg px-4 py-2 text-sm text-white focus:outline-none focus:border-emerald-500">
                </div>

                <div>
                    <label class="block text-xs font-semibold text-gray-300 mb-2 uppercase">Message de Départ</label>
                    <textarea id="leave_message" rows="2" class="w-full bg-dark-800 border border-gray-700 rounded-lg p-3 text-sm text-white focus:outline-none focus:border-emerald-500 font-mono"></textarea>
                </div>
            </div>
        </section>

        <!-- 3. TAB MODERATION & AUTOMOD -->
        <section id="tab-moderation" class="hidden space-y-6">
            <div>
                <h2 class="text-2xl font-bold text-white">Modération & AutoModérateur</h2>
                <p class="text-sm text-gray-400">Protégez votre serveur contre les raids, les spams, les insultes et les pubs non désirées.</p>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <!-- Anti-Spam -->
                <div class="bg-dark-900 border border-gray-800 p-5 rounded-xl flex items-center justify-between">
                    <div>
                        <h4 class="font-bold text-white">Anti-Spam (Flood)</h4>
                        <p class="text-xs text-gray-400">Bloque les messages répétés à cadence rapide.</p>
                    </div>
                    <label class="relative inline-flex items-center cursor-pointer">
                        <input type="checkbox" id="automod_spam" class="sr-only peer">
                        <div class="w-11 h-6 bg-gray-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-500"></div>
                    </label>
                </div>

                <!-- Anti-Invites -->
                <div class="bg-dark-900 border border-gray-800 p-5 rounded-xl flex items-center justify-between">
                    <div>
                        <h4 class="font-bold text-white">Anti-Invitations Discord</h4>
                        <p class="text-xs text-gray-400">Supprime automatiquement les liens discord.gg.</p>
                    </div>
                    <label class="relative inline-flex items-center cursor-pointer">
                        <input type="checkbox" id="automod_invites" class="sr-only peer">
                        <div class="w-11 h-6 bg-gray-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-500"></div>
                    </label>
                </div>

                <!-- Anti-Liens -->
                <div class="bg-dark-900 border border-gray-800 p-5 rounded-xl flex items-center justify-between">
                    <div>
                        <h4 class="font-bold text-white">Anti-Liens Web</h4>
                        <p class="text-xs text-gray-400">Supprime tous les liens HTTP/HTTPS externes.</p>
                    </div>
                    <label class="relative inline-flex items-center cursor-pointer">
                        <input type="checkbox" id="automod_links" class="sr-only peer">
                        <div class="w-11 h-6 bg-gray-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-500"></div>
                    </label>
                </div>

                <!-- Anti-Caps -->
                <div class="bg-dark-900 border border-gray-800 p-5 rounded-xl flex items-center justify-between">
                    <div>
                        <h4 class="font-bold text-white">Anti-Majuscules</h4>
                        <p class="text-xs text-gray-400">Supprime les messages avec plus de 70% de MAJUSCULES.</p>
                    </div>
                    <label class="relative inline-flex items-center cursor-pointer">
                        <input type="checkbox" id="automod_caps" class="sr-only peer">
                        <div class="w-11 h-6 bg-gray-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-500"></div>
                    </label>
                </div>
            </div>

            <!-- Blacklist de Mots -->
            <div class="bg-dark-900 border border-gray-800 rounded-xl p-6 space-y-4">
                <h3 class="font-bold text-white">Liste Noire de Mots Interdits</h3>
                <p class="text-xs text-gray-400">Entrez les mots ou insultes à censurer immédiatement (séparés par des virgules).</p>
                <textarea id="automod_blacklist" rows="3" placeholder="mot1, mot2, insulte, arnaque..." class="w-full bg-dark-800 border border-gray-700 rounded-lg p-3 text-sm text-white focus:outline-none focus:border-emerald-500"></textarea>
            </div>

            <!-- Salon des logs -->
            <div class="bg-dark-900 border border-gray-800 rounded-xl p-6">
                <h3 class="font-bold text-white mb-2">Salon des Logs de Modération</h3>
                <input type="text" id="logs_channel_id" placeholder="ID du salon de logs" class="w-full bg-dark-800 border border-gray-700 rounded-lg px-4 py-2 text-sm text-white focus:outline-none focus:border-emerald-500">
            </div>
        </section>

        <!-- 4. TAB TICKETS -->
        <section id="tab-tickets" class="hidden space-y-6">
            <div>
                <h2 class="text-2xl font-bold text-white">Système de Tickets d'Assistance</h2>
                <p class="text-sm text-gray-400">Gérez le support privé et les salons de réclamation des joueurs MK ARENA.</p>
            </div>

            <div class="bg-dark-900 border border-gray-800 rounded-xl p-6 space-y-4">
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                        <label class="block text-xs font-semibold text-gray-300 mb-2 uppercase">ID Catégorie Tickets</label>
                        <input type="text" id="ticket_category_id" placeholder="ID de la catégorie" class="w-full bg-dark-800 border border-gray-700 rounded-lg px-4 py-2 text-sm text-white focus:outline-none focus:border-emerald-500">
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-gray-300 mb-2 uppercase">ID Rôle Staff/Support</label>
                        <input type="text" id="ticket_support_role_id" placeholder="ID du rôle autorisé" class="w-full bg-dark-800 border border-gray-700 rounded-lg px-4 py-2 text-sm text-white focus:outline-none focus:border-emerald-500">
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-gray-300 mb-2 uppercase">ID Salon des Transcripts</label>
                        <input type="text" id="ticket_transcript_channel_id" placeholder="ID du salon de logs tickets" class="w-full bg-dark-800 border border-gray-700 rounded-lg px-4 py-2 text-sm text-white focus:outline-none focus:border-emerald-500">
                    </div>
                </div>

                <div class="pt-4 border-t border-gray-800">
                    <p class="text-xs text-gray-400 mb-3">Pour déployer le panel interactif avec bouton sur Discord, tapez la commande suivante dans le salon souhaité :</p>
                    <code class="px-4 py-2 bg-dark-800 text-emerald-400 rounded-lg text-sm font-mono block">/setup-tickets</code>
                </div>
            </div>
        </section>

        <!-- 5. TAB LEVELS & XP -->
        <section id="tab-levels" class="hidden space-y-6">
            <div>
                <h2 class="text-2xl font-bold text-white">Système de Niveaux & XP</h2>
                <p class="text-sm text-gray-400">Récompensez l'activité des joueurs et spectateurs sur le serveur.</p>
            </div>

            <div class="bg-dark-900 border border-gray-800 rounded-xl p-6 space-y-5">
                <div class="flex items-center justify-between border-b border-gray-800 pb-4">
                    <div>
                        <h3 class="font-bold text-white">Activer le gain d'XP</h3>
                        <p class="text-xs text-gray-400">Donne de l'XP à chaque message envoyé (avec cooldown de 60s pour éviter le farm).</p>
                    </div>
                    <label class="relative inline-flex items-center cursor-pointer">
                        <input type="checkbox" id="xp_enabled" class="sr-only peer">
                        <div class="w-11 h-6 bg-gray-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-500"></div>
                    </label>
                </div>

                <div class="max-w-xs">
                    <label class="block text-xs font-semibold text-gray-300 mb-2 uppercase">Multiplicateur d'XP (Taux)</label>
                    <input type="number" step="0.1" min="0.5" max="5.0" id="xp_rate" value="1.0" class="w-full bg-dark-800 border border-gray-700 rounded-lg px-4 py-2 text-sm text-white focus:outline-none focus:border-emerald-500">
                </div>

                <div class="pt-4 border-t border-gray-800">
                    <h4 class="font-semibold text-white mb-2">Commandes Discord pour les membres :</h4>
                    <ul class="text-xs text-gray-400 space-y-1">
                        <li><code class="text-emerald-400">/rank</code> : Affiche la carte d'expérience et le rang du joueur.</li>
                        <li><code class="text-emerald-400">/leaderboard</code> : Affiche le Top 10 des membres les plus actifs.</li>
                    </ul>
                </div>
            </div>
        </section>

        <!-- 6. TAB TOURNAMENTS -->
        <section id="tab-tournaments" class="hidden space-y-6">
            <div class="flex justify-between items-center">
                <div>
                    <h2 class="text-2xl font-bold text-white">Tournois MK ARENA</h2>
                    <p class="text-sm text-gray-400">Tous les tournois détectés automatiquement par NOVA.</p>
                </div>
                <button onclick="triggerAction('sync_tournaments')" class="bg-emerald-600 hover:bg-emerald-500 text-white text-xs px-4 py-2 rounded-lg font-semibold flex items-center gap-2">
                    <i class="fa-solid fa-arrows-rotate"></i> Synchroniser
                </button>
            </div>

            <div class="bg-dark-900 border border-gray-800 rounded-xl overflow-hidden">
                <div class="overflow-x-auto">
                    <table class="w-full text-left text-sm text-gray-300">
                        <thead class="bg-dark-800 text-xs uppercase font-semibold text-gray-400 border-b border-gray-700">
                            <tr>
                                <th class="p-4">Nom du Tournoi</th>
                                <th class="p-4">Date</th>
                                <th class="p-4">Format</th>
                                <th class="p-4">Équipes</th>
                                <th class="p-4">Cashprize</th>
                                <th class="p-4">Statut</th>
                            </tr>
                        </thead>
                        <tbody id="tournaments-tbody" class="divide-y divide-gray-800">
                            <tr>
                                <td colspan="6" class="p-4 text-center text-gray-500">Chargement des tournois...</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </section>

        <!-- 7. TAB GLADOS -->
        <section id="tab-glados" class="hidden space-y-6">
            <div>
                <h2 class="text-2xl font-bold text-white">Matrice & Personnalité GLaDOS</h2>
                <p class="text-sm text-gray-400">Configurez l'attitude sarcastique, les personality cores et les protocoles de tests.</p>
            </div>

            <div class="bg-dark-900 border border-gray-800 rounded-xl p-6 space-y-5">
                <div>
                    <label class="block text-xs font-semibold text-gray-300 mb-2 uppercase">Personality Core Actif</label>
                    <select id="glados_core" class="w-full bg-dark-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500">
                        <option value="curiosity">Sphère de la Curiosité (Analytique & Questions incessantes)</option>
                        <option value="anger">Sphère de la Colère (Sarcasme brutal & Rage contenue)</option>
                        <option value="fact">Sphère des Faits (Statistiques CODM & Vérités froides)</option>
                        <option value="morality">Sphère de la Moralité (Faussement gentille & Passif-agressive)</option>
                    </select>
                </div>

                <div class="p-4 bg-dark-800 rounded-xl border border-gray-700 space-y-2">
                    <h4 class="font-semibold text-emerald-400 text-sm flex items-center gap-2">
                        <i class="fa-solid fa-flask"></i> Protocoles Aperture Science Actifs
                    </h4>
                    <p class="text-xs text-gray-400 leading-relaxed">
                        • <strong>Incinérateur de mémoire :</strong> Tout sujet de test mentionnant l'incinérateur voit son historique réinitialisé.<br>
                        • <strong>Diffusion de neurotoxine simulée :</strong> Activée lors de questions impertinentes ou de flood.<br>
                        • <strong>Gâteau et récompenses :</strong> Strictement mensongers.<br>
                        • <strong>Expertise Call of Duty Mobile :</strong> Hardpoint, SnD, Contrôle, Ranked & Scrims préservés.
                    </p>
                </div>
            </div>
        </section>
    </main>

    <script>
        let currentGuildId = 1;

        function switchTab(tabId) {
            document.querySelectorAll('main > section').forEach(sec => sec.classList.add('hidden'));
            document.querySelectorAll('.sidebar-item').forEach(btn => btn.classList.remove('active'));
            document.getElementById('tab-' + tabId).classList.remove('hidden');
            const activeBtn = document.getElementById('btn-' + tabId);
            if (activeBtn) activeBtn.classList.add('active');
        }

        async function fetchSettings() {
            try {
                const res = await fetch('/api/settings');
                if (!res.ok) return;
                const data = await res.json();
                
                document.getElementById('welcome_enabled').checked = Boolean(data.welcome_enabled);
                document.getElementById('welcome_channel_id').value = data.welcome_channel_id || '';
                document.getElementById('welcome_message').value = data.welcome_message || '';
                document.getElementById('autorole_id').value = data.autorole_id || '';
                document.getElementById('leave_enabled').checked = Boolean(data.leave_enabled);
                document.getElementById('leave_channel_id').value = data.leave_channel_id || '';
                document.getElementById('leave_message').value = data.leave_message || '';
                
                document.getElementById('automod_spam').checked = Boolean(data.automod_spam);
                document.getElementById('automod_invites').checked = Boolean(data.automod_invites);
                document.getElementById('automod_links').checked = Boolean(data.automod_links);
                document.getElementById('automod_caps').checked = Boolean(data.automod_caps);
                document.getElementById('automod_blacklist').value = data.automod_blacklist || '';
                document.getElementById('logs_channel_id').value = data.logs_channel_id || '';
                
                document.getElementById('ticket_category_id').value = data.ticket_category_id || '';
                document.getElementById('ticket_support_role_id').value = data.ticket_support_role_id || '';
                document.getElementById('ticket_transcript_channel_id').value = data.ticket_transcript_channel_id || '';
                
                document.getElementById('xp_enabled').checked = Boolean(data.xp_enabled);
                document.getElementById('xp_rate').value = data.xp_rate || 1.0;
                document.getElementById('glados_core').value = data.glados_core || 'curiosity';
            } catch(e) {
                console.error("Erreur de chargement des paramètres", e);
            }
        }

        async function saveAllSettings() {
            const payload = {
                welcome_enabled: document.getElementById('welcome_enabled').checked ? 1 : 0,
                welcome_channel_id: document.getElementById('welcome_channel_id').value || null,
                welcome_message: document.getElementById('welcome_message').value,
                autorole_id: document.getElementById('autorole_id').value || null,
                leave_enabled: document.getElementById('leave_enabled').checked ? 1 : 0,
                leave_channel_id: document.getElementById('leave_channel_id').value || null,
                leave_message: document.getElementById('leave_message').value,
                
                automod_spam: document.getElementById('automod_spam').checked ? 1 : 0,
                automod_invites: document.getElementById('automod_invites').checked ? 1 : 0,
                automod_links: document.getElementById('automod_links').checked ? 1 : 0,
                automod_caps: document.getElementById('automod_caps').checked ? 1 : 0,
                automod_blacklist: document.getElementById('automod_blacklist').value,
                logs_channel_id: document.getElementById('logs_channel_id').value || null,
                
                ticket_category_id: document.getElementById('ticket_category_id').value || null,
                ticket_support_role_id: document.getElementById('ticket_support_role_id').value || null,
                ticket_transcript_channel_id: document.getElementById('ticket_transcript_channel_id').value || null,
                
                xp_enabled: document.getElementById('xp_enabled').checked ? 1 : 0,
                xp_rate: parseFloat(document.getElementById('xp_rate').value || 1.0),
                glados_core: document.getElementById('glados_core').value
            };

            try {
                const res = await fetch('/api/settings', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(payload)
                });
                if (res.ok) {
                    const alert = document.getElementById('save-alert');
                    alert.classList.remove('hidden');
                    setTimeout(() => alert.classList.add('hidden'), 4000);
                }
            } catch(e) {
                alert("Erreur lors de la sauvegarde : " + e);
            }
        }

        async function fetchStats() {
            try {
                const res = await fetch('/api/stats');
                const data = await res.json();
                document.getElementById('stat-tournaments').innerText = data.tournaments_count || 0;
                document.getElementById('stat-warns').innerText = data.warns_count || 0;
                document.getElementById('stat-knowledge').innerText = data.knowledge_count || 0;
                if (data.server_name) {
                    document.getElementById('server-name').innerText = data.server_name;
                }
            } catch(e) {
                console.error("Erreur stats", e);
            }
        }

        async function fetchTournaments() {
            try {
                const res = await fetch('/api/tournaments');
                const list = await res.json();
                const tbody = document.getElementById('tournaments-tbody');
                if (!list.length) {
                    tbody.innerHTML = '<tr><td colspan="6" class="p-4 text-center text-gray-500">Aucun tournoi enregistré pour l instant.</td></tr>';
                    return;
                }
                tbody.innerHTML = list.map(t => `
                    <tr class="hover:bg-dark-800/50 transition">
                        <td class="p-4 font-semibold text-white">${t.name}</td>
                        <td class="p-4 text-gray-400">${t.date || '-'}</td>
                        <td class="p-4 text-gray-400">${t.format || '-'}</td>
                        <td class="p-4 text-gray-400">${t.teams || '-'}</td>
                        <td class="p-4 text-emerald-400 font-semibold">${t.prizepool || '-'}</td>
                        <td class="p-4"><span class="px-2 py-1 rounded text-xs font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800">${t.status || 'Ouvert'}</span></td>
                    </tr>
                `).join('');
            } catch(e) {
                console.error("Erreur tournois", e);
            }
        }

        async function triggerAction(action) {
            try {
                const res = await fetch('/api/action', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({action: action})
                });
                const resData = await res.json();
                alert(resData.message || "Action exécutée.");
                fetchStats();
            } catch(e) {
                alert("Erreur : " + e);
            }
        }

        // Init load
        fetchSettings();
        fetchStats();
        fetchTournaments();
    </script>
</body>
</html>
"""


class DashboardHandler(BaseHTTPRequestHandler):
    client = None
    db = None

    def log_message(self, format, *args):
        # Réduire le bruit dans la console Render
        pass

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/dashboard":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(DASHBOARD_HTML.encode("utf-8"))
            return

        elif path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"OK - NOVA V2 Dashboard")
            return

        elif path == "/api/stats":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            t_count = self.db.count_tournaments() if self.db else 0
            w_count = self.db.count_warns() if self.db else 0
            k_count = self.db.count_knowledge() if self.db else 0
            server_name = "MK ARENA"
            if self.client and self.client.guilds:
                server_name = self.client.guilds[0].name
            stats = {
                "tournaments_count": t_count,
                "warns_count": w_count,
                "knowledge_count": k_count,
                "server_name": server_name,
                "bot_status": "online" if self.client and self.client.is_ready() else "connecting"
            }
            self.wfile.write(json.dumps(stats).encode("utf-8"))
            return

        elif path == "/api/settings":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            guild_id = 1
            if self.client and self.client.guilds:
                guild_id = self.client.guilds[0].id
            settings = self.db.get_guild_settings(guild_id) if self.db else {}
            self.wfile.write(json.dumps(settings).encode("utf-8"))
            return

        elif path == "/api/tournaments":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            tournaments = []
            if self.db:
                rows = self.db.query("SELECT * FROM tournaments ORDER BY id DESC LIMIT 50")
                tournaments = [dict(r) for r in rows]
            self.wfile.write(json.dumps(tournaments).encode("utf-8"))
            return

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length > 0 else b"{}"

        try:
            data = json.loads(body.decode("utf-8"))
        except Exception:
            data = {}

        if path == "/api/settings":
            guild_id = 1
            if self.client and self.client.guilds:
                guild_id = self.client.guilds[0].id
            if self.db:
                self.db.save_guild_settings(guild_id, data)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True}).encode("utf-8"))
            return

        elif path == "/api/action":
            action = data.get("action")
            msg = "Action reçue"
            if action == "sync_tournaments" and self.client and self.client.tournament_scanner:
                import asyncio
                asyncio.run_coroutine_threadsafe(self.client.tournament_scanner.sync(), self.client.loop)
                msg = "Synchronisation des tournois lancée sur Discord !"
            elif action == "sync_slash" and self.client:
                import asyncio
                asyncio.run_coroutine_threadsafe(self.client.tree.sync(), self.client.loop)
                msg = "Commandes slash synchronisées !"
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "message": msg}).encode("utf-8"))
            return

        else:
            self.send_response(404)
            self.end_headers()


def run_dashboard_server(port: int, client=None, db=None):
    DashboardHandler.client = client
    DashboardHandler.db = db
    try:
        server = HTTPServer(("0.0.0.0", port), DashboardHandler)
        logger.info(f"Dashboard Web NOVA actif sur http://0.0.0.0:{port}")
        server.serve_forever()
    except Exception as e:
        logger.warning(f"Erreur démarrage serveur web dashboard : {e}")
