from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from scan_manager.models import Host

from scan_manager.nmap_helper import * # get_ip etc

from netaddr import *
import os
import random
import sys
import traceback

# Create your views here.

def host(request):

  h = request.GET['h']

  host_data = Host.objects.filter(ip=h)

  context = {
    'host': h,
    'host_data' : host_data
    }

  return render(request,"host.html",context)

def search(request):
  # https://djangosnippets.org/snippets/1961/ <-- search by subnet

  try:
    page = int(request.GET['page'])
  except:
    page = 0

  try:
    q = request.GET['q']
  except:
    q = ""

  try:
    net = IPNetwork(request.GET['net'])
  except:
    net = IPNetwork("0.0.0.0/0")

  search = Host.objects.order_by('-mtime')

  if len(q) > 2:
    search = search.filter(data__search=q)

  # only apply filter for class b or smaller
  if len(net)<=65536:
    iplist = [ str(x) for x in list(net) ]
    search = search.filter(ip__in=iplist)

  context = {
    'query': q,
    'net':net ,
    'numresults': len(search) ,
    #'numresults': 0 ,
    'page':page ,
    'hosts': search[page*20:page*20+20] }
  return render(request,"search2.html",context)
  #return render(request,"search.html",context)

def getwork(request):

  random.seed(os.urandom(200))

  scope=[]
  try:
    for line in open("scope.txt"):
      scope.append(IPNetwork(line))

  except:
    print("failed to parse scope.txt")
    scope=[]
    scope.append(IPNetwork("0.0.0.0/0"))

  # how many hosts are in scope?
  magnitude = sum(len(network) for network in scope)
  
  # pick one
  index = random.randint(0,magnitude-1);

  target=""
  for network in scope:
    if index>=len(network):
      index-=len(network)
    else:
      target=network[index]
      break

  #return HttpResponse("google.com")
  return HttpResponse(target)

@csrf_exempt
def submit(request):

  data = str(request.body)
  data = data.replace('\\n','\n') # this is stupid

  try:
    ip = get_ip(data)
    hostname = get_hostname(data)
    ports = get_ports(data)
    country = get_country(ip)
  except Exception as e:
    return HttpResponse("you fucked it up!\n"+str(traceback.format_exc()))

  if len(ports) == 0:
    return HttpResponse("no open ports!")

  newhost, created=Host.objects.get_or_create(ip=ip)
  newhost.hostname = hostname
  newhost.ports = ports
  newhost.country = country
  newhost.data = request.body
  newhost.save()

  return HttpResponse("ip: "+ip+"\nhostname: "+hostname+"\nports: "+str(ports))

