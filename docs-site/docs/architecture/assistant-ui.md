# Architecture: Assistant UI Package

## Présentation
Le package `assistant-ui` a été refactorisé pour suivre une architecture Hexagonale (DDD) afin d'isoler la logique métier, la gestion d'état et la couche d'accès aux données.

## Structure
```
packages/assistant-ui/
├── src/
│   ├── application/     # Cas d'usage et gestion d'état (Zustand)
│   ├── config/          # Validation d'environnement (Zod)
│   ├── domain/          # Modèles (Session, Message) et Erreurs
│   ├── i18n/            # Internationalisation isolée (fr.json, en.json)
│   ├── infrastructure/  # Adaptateurs (GraphQL, LocalStorage)
│   └── ui/              # Composants React (AssistantRoot)
```

## Décisions clés
- **Isolation:** Le package est 100% découplé du reste de l'application Next.js (`apps/web`). Il exporte `<AssistantMascot />`.
- **I18n indépendant:** Utilisation d'un hook `useAssistantTranslation` natif au package pour garantir qu'il peut fonctionner sans le système d'i18n du conteneur.
- **Gestion d'état centralisée:** Utilisation de Zustand pour centraliser l'historique des sessions et la gestion du chat.
- **Feature Flag:** L'assistant vérifie `NEXT_PUBLIC_ENABLE_ASSISTANT_BETA`. S'il est `false`, le composant retourne `null`.
