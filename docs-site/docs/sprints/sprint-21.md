---
id: sprint-21
title: Sprint 21 — Architecture Hexagonale & Monorepo
sidebar_label: 🏃 Sprint 21
---

# Sprint 21 — Architecture Hexagonale & Monorepo

Ce sprint se concentre sur la stabilisation de l'infrastructure Michi 道 en adoptant les meilleures pratiques de développement modernes.

## 🎯 Objectifs
- ✅ Transformer la structure en **Monorepo** avec npm workspaces.
- ✅ Adopter l'**Architecture Hexagonale** (Ports & Adapteurs) pour le backend.
- ✅ Sécuriser le typage **Full-stack** avec GraphQL Codegen.
- ✅ Mettre en place la **Documentation Docusaurus 3**.

## 📊 Avancement des Épiques

### EPIC A — Monorepo & Restructuration `apps/`
| ID | User Story | Points | Statut |
|----|-----------|--------|--------|
| US 21.1 | Monorepo Setup | 5 | ✅ Done |
| US 21.3 | Package `ui` Design System | 5 | ✅ Done |
| US 21.5 | Mise à jour Makefile & Scripts | 3 | ✅ Done |

### EPIC B — Architecture DDD Hexagonale Backend
| ID | User Story | Points | Statut |
|----|-----------|--------|--------|
| US 21.6 | Domain Auth | 5 | ✅ Done |
| US 21.7 | Infrastructure Auth | 5 | ✅ Done |
| US 21.8 | Application Auth | 5 | ✅ Done |
| US 21.9 | Resolvers Auth minces | 8 | ✅ Done |
| US 21.10 | Domain + Infrastructure Inventory | 8 | ✅ Done |
| US 21.11 | Domain + Infrastructure Forecasting | 5 | ✅ Done |
| US 21.12 | DI Container | 3 | ✅ Done |
| US 21.13 | Fix Google OAuth async | 2 | ✅ Done |

### EPIC C — Typage Strict Bout en Bout
| ID | User Story | Points | Statut |
|----|-----------|--------|--------|
| US 21.14 | Typage Backend `mypy --strict` | 5 | ✅ Done |
| US 21.15 | Génération types GraphQL Frontend | 5 | ✅ Done |
| US 21.16 | Typage Frontend `tsc --strict` | 3 | ✅ Done |

### EPIC D — Documentation Docusaurus + API
| ID | User Story | Points | Statut |
|----|-----------|--------|--------|
| US 21.17 | Setup Docusaurus 3 | 5 | 🏗️ In Progress |
| US 21.19 | API Reference GraphQL | 5 | ✅ Done |

## 🧪 Qualité (Tests)
| Statut | Description |
|--------|-------------|
| ✅ Done | **US 21.24 :** Tests Core Backend (>85% App coverage) |
| ✅ Done | **US 21.25 :** Tests Composants Frontend |
| ✅ Done | **US 21.26 :** CI/CD GitHub Actions |
| 🏗️ In Progress | **US 21.22 :** E2E Auth Playwright |

:::info
Ce sprint est une étape cruciale pour permettre l'onboarding de nouveaux développeurs et assurer la scalabilité de la plateforme SaaS.
:::
