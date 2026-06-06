# Stage 1: Prune monorepo
FROM node:20-alpine AS pruner
RUN apk add --no-cache libc6-compat
WORKDIR /app
RUN npm install -g turbo
COPY . .
RUN turbo prune @michi/support --docker

# Stage 2: Install and Build
FROM node:20-alpine AS installer
RUN apk add --no-cache libc6-compat
WORKDIR /app

# First copy dependency files to leverage layer caching
COPY --from=pruner /app/out/json/ .
COPY --from=pruner /app/out/package-lock.json ./package-lock.json
RUN npm clean-install

# Copy project files and build
COPY --from=pruner /app/out/full/ .
COPY turbo.json turbo.json
RUN npx turbo run build --filter=@michi/support

# Stage 3: Minimal runner
FROM node:20-alpine AS runner
WORKDIR /app

# Don't run production container as root
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=installer /app/apps/support/package.json .
COPY --from=installer /app/apps/support/next.config.js .

# Standalone output folder containing minimal files
COPY --from=installer --chown=nextjs:nodejs /app/apps/support/.next/standalone ./
COPY --from=installer --chown=nextjs:nodejs /app/apps/support/.next/static ./apps/support/.next/static
COPY --from=installer --chown=nextjs:nodejs /app/apps/support/public ./apps/support/public

USER nextjs

EXPOSE 3002

ENV PORT 3002
ENV HOSTNAME "0.0.0.0"

CMD ["node", "apps/support/server.js"]
