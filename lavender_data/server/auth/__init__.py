from lavender_data.server.db import DbSession
from lavender_data.server.settings import AppSettings
from lavender_data.server.distributed import CurrentCluster
from lavender_data.server.cache import CacheClient

from .api_key_auth import api_key_auth
from .cluster_auth import cluster_auth
from .header import AuthorizationHeader


class AppAuth:
    """Merge auth methods with `or` operator.

    api_key_auth: bool
        If True, the api key auth will be applied.
    cluster_auth: bool
        If True, the cluster auth will be applied.
    """

    def __init__(self, api_key_auth: bool = False, cluster_auth: bool = False):
        self.api_key_auth = api_key_auth
        self.cluster_auth = cluster_auth

    def __call__(
        self,
        auth: AuthorizationHeader,
        session: DbSession,
        cluster: CurrentCluster,
        settings: AppSettings,
        cache: CacheClient,
    ):
        api_key_err = None
        if self.api_key_auth:
            try:
                return api_key_auth(auth, session, settings, cache, cluster)
            except Exception as e:
                api_key_err = e

        cluster_err = None
        if self.cluster_auth:
            try:
                return cluster_auth(auth, cluster, settings)
            except Exception as e:
                cluster_err = e

        raise api_key_err or cluster_err
